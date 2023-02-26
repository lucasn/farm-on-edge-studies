import os
from threading import Thread
from time import sleep
import paho.mqtt.client as mqtt
from json import loads, dumps
from socket import gethostbyname
from processing import process

CLOUD_LATENCY = int(os.environ['CLOUD_LATENCY'])
PROCESS_MESSAGE_FUNCTION_REPEAT = int(os.environ['PROCESS_MESSAGE_FUNCTION_REPEAT'])
PROCESS_MESSAGE_LEADING_ZEROS = int(os.environ['PROCESS_MESSAGE_LEADING_ZEROS'])

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
    sleep(2*CLOUD_LATENCY/1000) # Simulating incoming and outcoming latency
    process(leading_zeros=PROCESS_MESSAGE_LEADING_ZEROS, times=PROCESS_MESSAGE_FUNCTION_REPEAT)
    client.publish('client', message)

if __name__ == '__main__':
    main()