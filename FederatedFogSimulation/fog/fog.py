import paho.mqtt.client as mqtt
import time
import os

broker_ip = os.environ['broker_ip']
broker_port = int(os.environ['broker_port'])

client = mqtt.Client('fog')
client.connect(broker_ip, broker_port)

while True:
    client.publish("messages", os.environ['broker_message'].encode('utf-8'))
    time.sleep(1)