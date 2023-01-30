import paho.mqtt.client as mqtt
import os
from json import loads
from threading import Timer
from datetime import datetime

import matplotlib.pyplot as plt


QNT_FOGS = int(os.environ['QUANTITY_FOGS'])
BROKER_IP = os.environ['BROKER_IP']
BROKER_PORT = int(os.environ['BROKER_PORT'])
SIMULATION_TIME = int(os.environ['SIMULATION_TIME'])
WARMUP_TIME = float(os.environ['WARMUP_TIME'])

received_messages_counter = []
direct_messages_counter = []
redirect_messages_counter = []

cpu_usage = [[] for i in range(QNT_FOGS)]

is_collecting_data = True


def main():
    initialize_metrics_array()

    client = connect_to_broker(BROKER_IP, BROKER_PORT)

    client.subscribe('data')

    timer = Timer(WARMUP_TIME, start_simulation, args=(client, ))
    timer.start()
    
    client.loop_forever()


def on_message(client, userdata, message):
    if is_collecting_data:
        parsed_message = loads(message.payload)
        
        if parsed_message['data'] == 'MESSAGE_RECEIVED':
            received_messages_counter[parsed_message['id'] - 1] += 1

            if parsed_message['details'] == 'DIRECT':
                direct_messages_counter[parsed_message['id'] - 1] += 1
            
            else:
                redirect_messages_counter[parsed_message['id'] - 1] += 1

        if parsed_message['data'] == 'CPU_USAGE':
            cpu_usage[parsed_message['id'] - 1].append(parsed_message['cpu_usage'])


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Data collector connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def connect_to_broker(host, port):
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(host, port)
    return client


def initialize_metrics_array():
    global received_messages_counter
    global direct_messages_counter
    global redirect_messages_counter

    for i in range(QNT_FOGS):
        received_messages_counter.append(0)
        direct_messages_counter.append(0)
        redirect_messages_counter.append(0)


def start_simulation(client: mqtt.Client):
    print('Iniciando simulação...')
    client.publish('start')

    timer = Timer(SIMULATION_TIME, finish_simulation, args=(client,))
    timer.daemon = True
    timer.start()


def finish_simulation(client: mqtt.Client):
    global is_collecting_data

    is_collecting_data = False

    generate_figures()

    client.disconnect()


def generate_figures():
    print('Generating figures...')

    fogs_labels = []
    for i in range(QNT_FOGS):
        fogs_labels.append(f'Fog {i}')
    
    results_path = './results'
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    timestamp = datetime.now()

    plt.figure()
    plt.bar(fogs_labels, received_messages_counter)
    plt.title('Number of total messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/received_messages - {timestamp}.png')

    plt.figure()
    plt.bar(fogs_labels, direct_messages_counter)
    plt.title('Number of direct messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/direct_messages - {timestamp}.png')

    plt.figure()
    plt.bar(fogs_labels, received_messages_counter)
    plt.title('Number of redirected messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/redirect_messages - {timestamp}.png')

    # TODO: melhorar esse crime
    plt.figure()
    x = [i + 1 for i in range(len(cpu_usage[0]))]
    x_agora_vai = [x for i in range(QNT_FOGS)]
    plt.plot(x_agora_vai, cpu_usage)
    plt.legend([f'Fog {i + 1}' for i in range(QNT_FOGS)])
    plt.xlabel('Seconds')
    plt.ylabel('CPU Usage')
    plt.title('CPU Consumption by fog')
    plt.savefig(f'{results_path}/cpu_usage - {timestamp}.png')

if __name__ == '__main__':
    main()