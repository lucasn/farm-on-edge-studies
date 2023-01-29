import paho.mqtt.client as mqtt
from time import sleep
from random import randint
import concurrent.futures
import os
from datetime import datetime
from json import dumps

QNT_CLIENTS = int(os.environ['QUANTITY_CLIENTS'])
QNT_FOGS = int(os.environ['QUANTITY_FOGS'])

BROKER_IP = os.environ['BROKER_IP']
BROKER_PORT = int(os.environ['BROKER_PORT'])

def main():
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.connect(BROKER_IP, BROKER_PORT)

    with concurrent.futures.ThreadPoolExecutor(max_workers=QNT_CLIENTS) as executor:
        for i in range(QNT_CLIENTS):
            executor.submit(send_message, mqtt_client=client, client_id=(i + 1))
        

def send_message(mqtt_client, client_id):
    while True:
        selected_fog = randint(1, QNT_FOGS)

        sleep_time = randint(1, 4)

        message_id = datetime.now().isoformat()
        message = {
            'id': message_id,
            'type': 'DIRECT',
            'client_id': client_id,
            'route': [client_id]
        }
        message_topic = f'fog_{selected_fog}'

        print(f'Cliente {client_id} enviando mensagem para fog {selected_fog}')
        mqtt_client.publish(message_topic, dumps(message))
        sleep(sleep_time)


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected: {client}")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()