import paho.mqtt.client as mqtt
from config import BROKER_IP, BROKER_PORT
from time import sleep
from random import randint

def main():

    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.connect(BROKER_IP, BROKER_PORT)

    fog = 0
    while True:
        generate_linkset_id = randint(0, 10000)
        print(f'Enviando mensagem para fog {fog}')
        client.publish(f'fog_{fog}', f'{generate_linkset_id}#client1')
        sleep(2)
        client.publish(f'fog_{fog}', f'{generate_linkset_id}#client2')
        sleep(2)
        client.publish(f'fog_{fog}', f'{generate_linkset_id}#client3')
        sleep(2)
        fog = (fog + 1) % 4

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected: {client}")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()