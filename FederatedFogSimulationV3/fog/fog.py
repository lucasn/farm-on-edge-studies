import paho.mqtt.client as mqtt
import os
from queue import Queue
from copy import deepcopy
from random import randint
from time import sleep
from threading import Thread

from asymmetric_auction import hold_auction
from config import BROKER_IP, BROKER_PORT

FOG_ID = int(os.environ['fog_id'])
latency_table = []
fogs_number = 0

messages = Queue()


def main():
    global latency_table, fogs_number

    print(f'Id da fog atual: {FOG_ID}')

    fogs_number, latency_table = retrieve_latencies_mapping(FOG_ID)

    print(latency_table)
    print(f'Número de fogs: {fogs_number}')

    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(BROKER_IP, BROKER_PORT)
    client.subscribe(f'fog_{FOG_ID}')

    auction = Thread(target=run_auction, args=(client,), daemon=True)
    auction.start()

    client.loop_forever()

def run_auction(client):
    global messages, fogs_number, latency_table

    while True:

        while messages.empty():
            sleep(1)

        actual_latency_table = deepcopy(latency_table)

        auction_messages = []

        while not messages.empty() and len(auction_messages) < fogs_number:
            auction_messages.append(messages.get())
        
        latency_benefits = []
        messages_number = len(auction_messages)
        print(f'Processando {messages_number} mensagens')    

        actual_latency_table = generate_actual_latency_table(actual_latency_table)

        for i in range(messages_number):
            for j in range(fogs_number):
                latency_benefits.append(actual_latency_table)

        results = hold_auction(fogs_number, messages_number, latency_benefits)

        for i, fog in enumerate(results):
            message_id, message = auction_messages[i].split('#')
            print(f'Mensagem {i} -> Fog {results[i]}')
            client.publish(f'fog_{results[i]}', f'0#{message} -> fog {FOG_ID}')


def on_message(client, userdata, message):
    global messages, latency_table

    decoded_message = message.payload.decode("utf-8")
    message_id, message = str(decoded_message).split('#')

    print(f'Id da mensagem: {message_id}')
    print(f'Mensagem: {message}')

    if message_id == '0':
        print('Enviando mensagem pra a nuvem')
        client.publish('cloud', message + f' -> fog_{FOG_ID}')
    else:
        messages.put(decoded_message)


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Fog {FOG_ID} connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def retrieve_latencies_mapping(fog_id):
    latency_file = open('./latency_table.txt', 'r')
    fogs_number, lines_number = latency_file.readline().split(' - ')

    fogs_number = int(fogs_number)
    lines_number = int(lines_number)

    latency_table = []
    inverted_latency_table = []
    for i in range(fogs_number):
        latency_table.append(0)
        inverted_latency_table.append(0)

    for i in range(lines_number):
        fog1, fog2, latency = latency_file.readline().split(' - ')

        if int(fog1) == fog_id:
            latency_table[int(fog2)] = int(latency)
        if int(fog2) == fog_id:
            latency_table[int(fog1)] = int(latency)

    max_latency = 0
    for i in range(fogs_number):
        max_latency = max(max_latency, latency_table[i])

    for i in range(fogs_number):
        if latency_table[i] > 0:
            inverted_latency_table[i] = max_latency - latency_table[i]

    return fogs_number, inverted_latency_table


def generate_actual_latency_table(latency_table):
    actual_latency_table = []
   
    for latency in latency_table:
        if latency > 0:
            error = randint(0, 20) - 10
            actual_latency_table.append(latency + error)
        else:
            actual_latency_table.append(0)
    return actual_latency_table


if __name__ == '__main__':
    main()