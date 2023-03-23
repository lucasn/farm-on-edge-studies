import paho.mqtt.client as mqtt
import os
from queue import Queue
from copy import deepcopy
from threading import Thread, Timer, Condition
from json import dumps, loads
import docker
from socket import gethostbyname
from processing import process
from ping import ping
from time import sleep, time
import random

from asymmetric_auction import hold_auction

FOG_ID = None
QUANTITY_FOGS = int(os.environ['QUANTITY_FOGS'])
MESSAGE_PROCESSING_CPU_THRESHOLD = int(os.environ['MESSAGE_PROCESSING_CPU_THRESHOLD'])
PROCESS_MESSAGE_LEADING_ZEROS = int(os.environ['PROCESS_MESSAGE_LEADING_ZEROS'])
PROCESS_MESSAGE_FUNCTION_REPEAT = int(os.environ['PROCESS_MESSAGE_FUNCTION_REPEAT'])
ACTIVATE_AUCTION = bool(int(os.environ['ACTIVATE_AUCTION']))

federation_info = {
    'latency': [0] * (QUANTITY_FOGS + 1), # we add 1 because we consider that fog 0 is the cloud
    'cpu_usage': [0] * (QUANTITY_FOGS + 1)
}   

cpu_usage = 0.0

message_queue = Queue()

cpu_usage_mutex = Condition()
message_queue_mutex = Condition()

def main():
    if ACTIVATE_AUCTION:
        print("[SIMULATION] Simulation with auction")
    else:
        print("[SIMULATION] Simulation without auction")

    client = connect_to_broker(gethostbyname('mosquitto'), 1883)
    client.subscribe('start_fogs')

    client.loop_forever()


def start_simulation(client):
    container = retrieve_this_container()

    retrieve_fog_id(container)

    client.subscribe(f'fog_{FOG_ID}')

    RepeatTimer(interval=2, function=request_federation_info, args=(client,)).start()

    handle_messages_thread = Thread(target=handle_messages, args=(client,))
    handle_messages_thread.start()


def retrieve_this_container():
    container_id = os.environ['HOSTNAME']

    docker_client = docker.from_env()

    for container in docker_client.containers.list():
        if container_id == container.id[:len(container_id)]:
            return container
        
    raise Exception('Cannot retrieve the container')


def update_cpu_usage(container):
    global cpu_usage, cpu_usage_mutex

    stream = container.stats(decode=True)
    next(stream)

    while True:
        stats = next(stream)
        with cpu_usage_mutex:
            cpu_usage = retrieve_cpu_usage_from_docker_stats(stats)
            #print(f'[RESOURCES] CPU utilization: {cpu_usage}\n', end='')
            cpu_usage_mutex.notify_all()
        

def retrieve_cpu_usage_from_docker_stats(stats):
    online_cpus = stats['cpu_stats']['online_cpus']
    delta_container = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']

    delta_system = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    cpu_percent = (delta_container / delta_system) * online_cpus * 100
    
    return cpu_percent


def connect_to_broker(host, port):
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(host, port)

    return client


def send_to_fog(client, fog, message):
    global latency_table
    print(f'[DEBUG] Latency to send message to fog {fog}: {latency_table[fog]}\n', end='')

    message['time_in_fog'] += calculate_time_in_fog(message)

    sleep(latency_table[fog] / 1000)
    client.publish(f'fog_{fog}', dumps(message))


def calculate_time_in_fog(message):
    arrival_time = message['arrival_time']
    del message['arrival_time']
    exit_time = time()
    return exit_time - arrival_time


def run_auction(client: mqtt.Client, auction_messages: list):
    global latency_table

    actual_latency_table = deepcopy(latency_table)

    del actual_latency_table[0] # removing the cloud from the auction
    
    latency_benefits = []
    messages_number = len(auction_messages)
    #print(f'[AUCTION] Running auction for {messages_number} messages')

    #print(f'[x] Tabela de latências para o leilão: {actual_latency_table}')
    actual_latency_table = transform_latency(actual_latency_table)
    #print(f'[x] Tabela transformada: {actual_latency_table}')


    for i, value in enumerate(actual_latency_table):
        actual_latency_table[i] = int(round(value, 3) * 1000)

    #print(f'[DEBUG] Actual Latency table: {actual_latency_table}')

    for i in range(messages_number):
        for j in range(QUANTITY_FOGS):
            latency_benefits.append(actual_latency_table)



    #print(f'[DEBUG] Tabela de benefícios: {latency_benefits}')

    # the return for the auction algorithm is a array where the indexes
    # are the messages are the values in the indexes are the fogs that
    # match those messages
    results = hold_auction(QUANTITY_FOGS, messages_number, latency_benefits, (1/messages_number) - 0.0001)

    # we add 1 to the destination fog value because the fogs are indexed in 1
    for message_index, destination_fog in enumerate(results):
        message = auction_messages[message_index]

        message['route'].append(FOG_ID)
        message['type'] = 'REDIRECT'

        print(f'[AUCTION] Enviando mensagem {message_index} para fog {destination_fog + 1}')
        Thread(target=send_to_fog, args=(client, destination_fog + 1, message)).start()


def on_message(client: mqtt.Client, userdata, message):
    global message_queue, latency_table, message_queue_mutex

    if message.topic == 'start_fogs':
        print('[SIMULATION] Starting simulation...')
        Thread(target=start_simulation, args=(client,)).start()
        return

    parsed_message = loads(message.payload)
    parsed_message['arrival_time'] = time()

    data_report_message = {
        'id': FOG_ID,
        'data': 'MESSAGE_RECEIVED'
    }
    data_report_message['type'] = parsed_message['type']

    client.publish('data', dumps(data_report_message))
    
    if parsed_message['type'] == 'REQUEST_FEDERATION_INFO':
        handle_request_federation_info(client, parsed_message)

    elif parsed_message['type'] in ['DIRECT', 'REDIRECT']:
        with message_queue_mutex:
            message_queue.put(parsed_message)
            if message_queue.qsize() >= QUANTITY_FOGS - 1:
                send_to_auction_or_to_cloud(client)
            message_queue_mutex.notify_all()


def handle_request_federation_info(client, parsed_message):
    response = dumps({
        'id': FOG_ID,
        'type': 'RESPONSE_FEDERATION_INFO',
        'request_sent_time': parsed_message['sent_time'],
        'cpu_usage': cpu_usage 
    })

    sender_fog = parsed_message['id']

    client.publish(f'fog_{sender_fog}', response)


def handle_messages(client: mqtt.Client):
    global cpu_usage, cpu_usage_mutex, message_queue_mutex, message_queue

    while True:
        if cpu_usage < MESSAGE_PROCESSING_CPU_THRESHOLD:
            with message_queue_mutex:
                qnt_messages = message_queue.qsize()
                if qnt_messages == 0:
                    message_queue_mutex.wait()

                else:
                    message = message_queue.get()
                    process_thread = Thread(target=process_message, args=(client, message))
                    process_thread.start()

        else:
            with cpu_usage_mutex:
                cpu_usage_mutex.wait_for(cpu_usage_condition)


def send_to_auction_or_to_cloud(client):
    redirect_messages = []
        
    for _ in range(QUANTITY_FOGS-1):
        message = message_queue.get()
        if message['type'] == 'DIRECT':
            redirect_messages.append(message)
        else:
            message['route'].append(FOG_ID)
            message['time_in_fog'] += calculate_time_in_fog(message)
            client.publish('cloud', dumps(message))
    
    if len(redirect_messages) > 0:
        if ACTIVATE_AUCTION:
            Thread(target=run_auction, args=(client, redirect_messages)).start()
            data_report_message = {
                'id': FOG_ID,
                'data': 'AUCTION_PERFORMED'
            }
            client.publish('data', dumps(data_report_message))
        else:
            Thread(target=map_requests_to_fogs, args=(client, redirect_messages)).start()


def map_requests_to_fogs(client, messages):
    fogs_mapped = random.sample(range(1, QUANTITY_FOGS + 1), len(messages))
    for fog, message in zip(fogs_mapped, messages):
        message['type'] = 'REDIRECT'
        message['route'].append(FOG_ID)
        Thread(target=send_to_fog, args=(client, fog, message)).start()


def cpu_usage_condition():
    global cpu_usage
    return cpu_usage < MESSAGE_PROCESSING_CPU_THRESHOLD


def process_message(client: mqtt.Client, message: dict):
    process(leading_zeros=PROCESS_MESSAGE_LEADING_ZEROS, times=PROCESS_MESSAGE_FUNCTION_REPEAT)
    message['route'].append(FOG_ID)
    message['time_in_fog'] += calculate_time_in_fog(message)
    client.publish('client', dumps(message))
    #print('[x] Mensagem processada')


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Fog connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def retrieve_fog_id(container):
    global FOG_ID
    FOG_ID = int(container.name.split('-')[2])
    print(F'[SIMULATION] Fog Id Retrieved: {FOG_ID}')


def transform_latency(latency_table):
    max_latency = max(latency_table)

    transformed_latency = []
    for latency in latency_table:
        if latency > 0:
            transformed_latency.append(max_latency - latency + 1)
        else:
            transformed_latency.append(0)
    
    return transformed_latency


def request_federation_info(client):
    for i in range(1, QUANTITY_FOGS + 1):
        if i != FOG_ID:
            message = dumps({
                'id': FOG_ID,
                'type': 'REQUEST_FEDERATION_INFO',
                'sent_time': time()
            })
            client.publish(f'fog_{i}', message)
            

class RepeatTimer(Timer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs) 

if __name__ == '__main__':
    main()
