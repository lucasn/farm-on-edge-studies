import paho.mqtt.client as mqtt
import os
from config import BROKER_IP, BROKER_PORT
from json import loads
from threading import Timer

import matplotlib.pyplot as plt

NUMBER_OF_FOGS = int(os.environ['NUMBER_OF_FOGS'])

received_messages_counter = []
direct_messages_counter = []
redirect_messages_counter = []

figure_generation_has_started = False

def main():
    for i in range(NUMBER_OF_FOGS):
        received_messages_counter.append(0)
        direct_messages_counter.append(0)
        redirect_messages_counter.append(0)

    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(BROKER_IP, BROKER_PORT)
    client.subscribe(f'data')

    timer = Timer(10, generate_figures)
    timer.daemon = True
    timer.start()

    client.loop_forever()

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Data collector connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, message):
    if figure_generation_has_started:
        return

    parsed_message = loads(message.payload)
    
    if parsed_message['data'] == 'MESSAGE_RECEIVED':
        received_messages_counter[parsed_message['id']] += 1

        if parsed_message['details'] == 'DIRECT':
            direct_messages_counter[parsed_message['id']] += 1
        
        else:
            redirect_messages_counter[parsed_message['id']] += 1


def generate_figures():
    global figure_generation_has_started
    figure_generation_has_started = True

    print('Generating figures...')

    fogs_labels = []
    for i in range(NUMBER_OF_FOGS):
        fogs_labels.append(f'Fog {i}')
    
    print(fogs_labels, received_messages_counter)

    plt.bar(fogs_labels, received_messages_counter)
    plt.savefig('received_messages.png')


if __name__ == '__main__':
    main()