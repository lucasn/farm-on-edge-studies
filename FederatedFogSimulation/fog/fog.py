import paho.mqtt.client as mqtt
from random import randrange, uniform
import time

mqtt_broker = '192.168.0.8'

client = mqtt.Client('temperature')
client.connect(mqtt_broker)

while True:
    randNumber = uniform(20.0, 21.0)
    client.publish("TEMPERATURE", randNumber)
    print("Just published " + str(randNumber) + " to topic TEMPERATURE")
    time.sleep(1)