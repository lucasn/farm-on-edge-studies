import paho.mqtt.client as mqtt
import os
from queue import Queue
from copy import deepcopy
from random import randint
from time import sleep, time
from threading import Thread, Timer
from json import dumps, loads
import docker
import psutil

from asymmetric_auction import hold_auction

FOG_ID = None
BROKER_PORT = int(os.environ['BROKER_PORT'])
BROKER_IP = os.environ['BROKER_IP']
QNT_FOGS = int(os.environ['QUANTITY_FOGS'])

latency_table = [0] * (QNT_FOGS + 1) # we add 1 because we consider that fog 0 is the cloud

cpu_times_counter = 1

messages = Queue()

def main():
    initialize()

    client = connect_to_broker(BROKER_IP, BROKER_PORT)
    client.subscribe(f'fog_{FOG_ID}')
    client.subscribe('start')

    auction = Thread(target=run_auction, args=(client,), daemon=True)
    auction.start()

    ping_thread = Thread(target=ping, args=(client,), daemon=True)
    ping_thread.start()

    client.loop_forever()


def retrieve_fog_id():
    container_id = os.environ['HOSTNAME']

    docker_client = docker.from_env()

    for container in docker_client.containers.list():
        if container_id == container.id[:len(container_id)]:
            fog_id = container.name.split('-')[2]
            return int(fog_id)
        
    raise Exception('Cannot retrieve container name')


def report_cpu_usage(client: mqtt.Client):
    global cpu_times_counter

    print('Enviando consumo de cpu')

    message = {
        'id': FOG_ID,
        'data': 'CPU_USAGE',
        'second': cpu_times_counter,
        'cpu_usage': psutil.cpu_percent(interval=0.1) # using the minimum interval recommended by the library
    }

    client.publish('data', dumps(message))

    cpu_times_counter += 1


def connect_to_broker(host, port):
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(host, port)

    return client


def initialize():
    global FOG_ID

    FOG_ID = retrieve_fog_id()

    map_latencies()


def run_auction(client):
    global messages, latency_table

    while True:
        while messages.empty():
            sleep(1)

        actual_latency_table = deepcopy(latency_table)

        del actual_latency_table[0] # removing the cloud from the auction

        auction_messages = []

        while not messages.empty() and len(auction_messages) < QNT_FOGS:
            auction_messages.append(messages.get())

        # we subtract 1 from QNT_FOGS because we don't want to consider the actual fog in the auction
        while not messages.empty() and len(auction_messages) < QNT_FOGS - 1:
            auction_messages.append(messages.get())
        
        latency_benefits = []
        messages_number = len(auction_messages)
        print(f'Processando {messages_number} mensagens')    

        print(f'[x] Tabela de latências para o leilão: {actual_latency_table}')
        actual_latency_table = transform_latency(actual_latency_table)
        print(f'[x] Tabela transformada: {actual_latency_table}')

        for i in range(messages_number):
            for j in range(QNT_FOGS):
                latency_benefits.append(actual_latency_table)

        # the return for the auction algorithm is a array where the indexes
        # are the messages are the values in the indexes are the fogs that
        # match those messages
        results = hold_auction(QNT_FOGS, messages_number, latency_benefits)

        # we add 1 to the destination fog value because the fogs are indexed in 1
        for message_index, destination_fog in enumerate(results):
            message = auction_messages[message_index]

            message['route'].append(FOG_ID)
            message['type'] = 'REDIRECT'

            print(f'Enviando mensagem {message_index} para fog {destination_fog + 1}')
            client.publish(f'fog_{destination_fog + 1}', dumps(message))


def on_message(client, userdata, message):
    global messages, latency_table

    if message.topic == 'start':
        cpu_usage_timer = RepeatTimer(interval=1, function=report_cpu_usage, args=(client,))
        cpu_usage_timer.start()
        return

    data_report_message = {
        'id': FOG_ID,
        'data': 'MESSAGE_RECEIVED'
    }

    parsed_message = loads(message.payload)

    if parsed_message['type'] == 'REDIRECT':
        print('Enviando mensagem pra a nuvem')

        parsed_message['route'].append(FOG_ID)
        client.publish('cloud', dumps(parsed_message))

        data_report_message['details'] = 'REDIRECT'
        client.publish('data', dumps(data_report_message))
    
    elif parsed_message['type'] == 'PING':
        ping_time = parsed_message['ping_time']
        source_fog_id = parsed_message['fog_id']

        response = {
            'type': 'PING_RESPONSE',
            'fog_id': FOG_ID,
            'ping_time': ping_time
        }
        
        response_thread = Thread(target=response_ping, args=(client, source_fog_id, dumps(response)))
        response_thread.start()
    
    elif parsed_message['type'] == 'PING_RESPONSE':
        start_time = parsed_message['ping_time']
        destination_fog = parsed_message['fog_id']
        end_time = time()

        latency_table[destination_fog] = int( 1000*(end_time - start_time) )

        print(f'[*] Latência para {destination_fog}: {latency_table[destination_fog]} ms')

    else:
        print(f'[x] Mensagem recebida para leilão')
        messages.put(parsed_message)
        data_report_message['details'] = 'DIRECT'
        client.publish('data', dumps(data_report_message))



def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Fog {FOG_ID} connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def map_latencies():
    with open('./latency_table.json', 'r') as f:
        latency_file = f.read()
        latencies = loads(latency_file)['latencies']

        for mapping in latencies:
            fog1, fog2 = mapping['between']
            latency = mapping['latency']

            if fog1 == FOG_ID:
                latency_table[fog2] = latency
            if fog2 == FOG_ID:
                latency_table[fog1] = latency


def transform_latency(latency_table):
    max_latency = max(latency_table)

    transformed_latency = []
    for latency in latency_table:
        if latency > 0:
            transformed_latency.append(max_latency - latency + 1)
        else:
            transformed_latency.append(0)
    
    return transformed_latency


def ping(client: mqtt.Client):
    global latency_table
    print('[-] Executando ping')
    while True:
        sleep(10)
        for i in range(QNT_FOGS):
            actual_fog = i + 1  # because fog 0 is the cloud
            if latency_table[actual_fog] > 0 and actual_fog != FOG_ID:
                ping_message = {
                    'type': 'PING',
                    'ping_time': time(),
                    'fog_id': FOG_ID
                }
                client.publish(f'fog_{actual_fog}', dumps(ping_message))


def response_ping(client: mqtt.Client, source_fog_id: int, response: str):
    latency_offset = randint(60, 100)
    sleep(latency_offset/1000)
    client.publish(f'fog_{source_fog_id}', response)

class RepeatTimer(Timer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs) 

if __name__ == '__main__':
    main()
