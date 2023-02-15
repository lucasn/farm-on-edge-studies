import os
from threading import Thread
from time import sleep
import paho.mqtt.client as mqtt
from json import loads, dumps
from socket import gethostbyname

CLOUD_LATENCY = int(os.environ['CLOUD_LATENCY'])

def main():
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(gethostbyname('mosquitto'), 1883)
    client.subscribe('cloud')

    client.loop_forever()

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Cloud connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, message):
    Thread(target=response_with_delay, args=(client, message.payload)).start()

    data_report_message = {
        'id': 0,
        'data': 'MESSAGE_RECEIVED',
        'type': 'CLOUD'
    }

    client.publish('data', dumps(data_report_message))

def response_with_delay(client: mqtt.Client, message:str):
    sleep(CLOUD_LATENCY/1000)
    client.publish('client', message)

if __name__ == '__main__':
    main()