import paho.mqtt.client as mqtt
import os
from config import BROKER_IP, BROKER_PORT


def main():
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(BROKER_IP, BROKER_PORT)
    client.subscribe(f'cloud')

    client.loop_forever()

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Cloud connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, message):
    print(f'Mensagem recebida: {str(message.payload.decode("utf-8"))}')

if __name__ == '__main__':
    main()