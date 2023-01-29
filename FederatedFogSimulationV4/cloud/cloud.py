import paho.mqtt.client as mqtt
from json import loads
import os

BROKER_IP = os.environ['BROKER_IP']
BROKER_PORT = int(os.environ['BROKER_PORT'])

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
    print(f'Mensagem recebida: {loads(message.payload)}')

if __name__ == '__main__':
    main()