import paho.mqtt.client as mqtt
from time import sleep, time
from random import randint
import concurrent.futures
import os
from datetime import datetime
from json import dumps, loads
import threading
from socket import gethostbyname

QNT_CLIENTS = int(os.environ['QUANTITY_CLIENTS'])
QNT_FOGS = int(os.environ['QUANTITY_FOGS'])

messages_sent_time = {}

def main():
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(gethostbyname('mosquitto'), 1883)
    client.subscribe('client')
    client.subscribe('start')

    client.loop_forever()

        
def send_message(mqtt_client, client_id):
    while True:
        selected_fog = randint(1, QNT_FOGS)

        message_id = datetime.now().isoformat()
        message = {
            'id': message_id,
            'type': 'DIRECT',
            'client_id': client_id,
            'route': [client_id]
        }
        message_topic = f'fog_{selected_fog}'

        mqtt_client.publish(message_topic, dumps(message))

        messages_sent_time[message_id] = time()

        sleep_time = randint(1, 4)
        sleep(sleep_time)


def create_client_threads(client: mqtt.Client):
    with concurrent.futures.ThreadPoolExecutor(max_workers=QNT_CLIENTS) as executor:
        for i in range(QNT_CLIENTS):
            executor.submit(send_message, mqtt_client=client, client_id=(i + 1))


def on_message(client, userdata, message):
    if message.topic == 'start':
        client_thread = threading.Thread(target=create_client_threads, args=(client,))
        client_thread.start()
        return

    parsed_message = loads(message.payload)

    start_time = messages_sent_time[parsed_message['id']]

    if start_time is not None:
        print(f'Mensagem {parsed_message["id"]} recebida | Tempo de resposta: {time() - start_time} s')
    
    else:
        print('Mensagem inesperada recebida')


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected: {client}")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()