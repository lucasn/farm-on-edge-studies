import paho.mqtt.client as mqtt
import os
from queue import Queue
from copy import deepcopy
from threading import Thread, Timer
from json import dumps, loads
import docker
from socket import gethostbyname
from processing import process
from ping import ping
from time import sleep

from asymmetric_auction import hold_auction

FOG_ID = None
QUANTITY_FOGS = int(os.environ['QUANTITY_FOGS'])
MESSAGE_PROCESSING_CPU_THRESHOLD = int(os.environ['MESSAGE_PROCESSING_CPU_THRESHOLD'])
PROCESS_MESSAGE_LEADING_ZEROS = int(os.environ['PROCESS_MESSAGE_LEADING_ZEROS'])
PROCESS_MESSAGE_FUNCTION_REPEAT = int(os.environ['PROCESS_MESSAGE_FUNCTION_REPEAT'])

latency_table = [0] * (QUANTITY_FOGS + 1) # we add 1 because we consider that fog 0 is the cloud
cpu_usage = 0.0

messages = Queue()

def main():
    container = retrieve_this_container()

    retrieve_fog_id(container)

    ping_all_fogs()

    client = connect_to_broker(gethostbyname('mosquitto'), 1883)
    client.subscribe(f'fog_{FOG_ID}')

    auction = Thread(target=run_auction, args=(client,), daemon=True)
    auction.start()

    ping_thread = Thread(target=execute_ping, daemon=True)
    ping_thread.start()

    update_cpu_thread = Thread(target=update_cpu_usage, args=(container,))
    update_cpu_thread.start()

    client.loop_forever()


def retrieve_this_container():
    container_id = os.environ['HOSTNAME']

    docker_client = docker.from_env()

    for container in docker_client.containers.list():
        if container_id == container.id[:len(container_id)]:
            return container
        
    raise Exception('Cannot retrieve the container')


def update_cpu_usage(container):
    global cpu_usage

    stream = container.stats(decode=True)
    next(stream)

    while True:
        stats = next(stream)
        cpu_usage = retrieve_cpu_usage_from_docker_stats(stats)


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


# TODO: Review the time between the running of the auction
def run_auction(client):
    global messages, latency_table

    while True:
        while messages.empty():
            sleep(1)

        actual_latency_table = deepcopy(latency_table)

        del actual_latency_table[0] # removing the cloud from the auction

        auction_messages = []

        # we subtract 1 from QNT_FOGS because we don't want to consider the actual fog in the auction
        while not messages.empty() and len(auction_messages) < QUANTITY_FOGS - 1:
            auction_messages.append(messages.get())
        
        latency_benefits = []
        messages_number = len(auction_messages)
        print(f'Processando {messages_number} mensagens')    

        print(f'[x] Tabela de latências para o leilão: {actual_latency_table}')
        actual_latency_table = transform_latency(actual_latency_table)
        print(f'[x] Tabela transformada: {actual_latency_table}')

        for i in range(messages_number):
            for j in range(QUANTITY_FOGS):
                latency_benefits.append(actual_latency_table)

        # the return for the auction algorithm is a array where the indexes
        # are the messages are the values in the indexes are the fogs that
        # match those messages
        results = hold_auction(QUANTITY_FOGS, messages_number, latency_benefits)

        # we add 1 to the destination fog value because the fogs are indexed in 1
        for message_index, destination_fog in enumerate(results):
            message = auction_messages[message_index]

            message['route'].append(FOG_ID)
            message['type'] = 'REDIRECT'

            print(f'Enviando mensagem {message_index} para fog {destination_fog + 1}')
            client.publish(f'fog_{destination_fog + 1}', dumps(message))


def on_message(client, userdata, message):
    global messages, latency_table

    parsed_message = loads(message.payload)
    
    if parsed_message['type'] in ['DIRECT', 'REDIRECT']:
        handle_message(client, parsed_message)


def handle_message(client: mqtt.Client, message: dict):
    global cpu_usage

    if cpu_usage < MESSAGE_PROCESSING_CPU_THRESHOLD:
        process_thread = Thread(target=process_message, args=(client, message))
        process_thread.start()

    else:
        if message['type'] == 'DIRECT':
            print(f'[x] Mensagem recebida para leilão')
            messages.put(message)
        
        else:
            print('[x] Mensagem enviada para a nuvem')
            message['route'].append(FOG_ID)
            client.publish('cloud', dumps(message))

    data_report_message = {
        'id': FOG_ID,
        'data': 'MESSAGE_RECEIVED'
    }

    data_report_message['details'] = message['type']
    client.publish('data', dumps(data_report_message))


def process_message(client: mqtt.Client, message:dict):
    process(leading_zeros=PROCESS_MESSAGE_LEADING_ZEROS, times=PROCESS_MESSAGE_FUNCTION_REPEAT)
    client.publish('client', dumps(message))
    print('[x] Mensagem processada')


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Fog {FOG_ID} connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def retrieve_fog_id(container):
    global FOG_ID
    FOG_ID = int(container.name.split('-')[2])


def transform_latency(latency_table):
    max_latency = max(latency_table)

    transformed_latency = []
    for latency in latency_table:
        if latency > 0:
            transformed_latency.append(max_latency - latency + 1)
        else:
            transformed_latency.append(0)
    
    return transformed_latency


def execute_ping():
    print('[-] Executando ping')
    while True:
        sleep(10)
        ping_all_fogs()
        

def ping_all_fogs():
    global latency_table
    for i in range(1, QUANTITY_FOGS + 1):
            if i != FOG_ID:
                latency = ping(f'simulation-fog-{i}')
                latency_table[i] = float(latency)
                print(f'[*] Latência para {i}: {latency_table[i]} ms')

    print(latency_table)

class RepeatTimer(Timer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs) 

if __name__ == '__main__':
    main()
