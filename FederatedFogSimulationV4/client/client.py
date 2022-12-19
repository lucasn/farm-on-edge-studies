import paho.mqtt.client as mqtt
from config import BROKER_IP, BROKER_PORT
from time import sleep
from random import randint
import concurrent.futures

QNT_CLIENTS = 30

def main():
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.connect(BROKER_IP, BROKER_PORT)

    with concurrent.futures.ThreadPoolExecutor(max_workers=QNT_CLIENTS) as executor:
        for i in range(QNT_CLIENTS):
            executor.submit(send_message, mqtt_client=client, client_id=(i + 1))
        

def send_message(mqtt_client, client_id):
    while True:
        fog = randint(0, 3)
        sleep_time = randint(1, 4)
        generate_linkset_id = randint(0, 10000)
        print(f'Client {client_id} enviando mensagem para fog {fog}\n', end='')
        mqtt_client.publish(f'fog_{fog}', f'{generate_linkset_id}#{client_id}')
        sleep(sleep_time)


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected: {client}")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()