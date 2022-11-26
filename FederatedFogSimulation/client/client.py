import paho.mqtt.client as mqtt
import os

def on_message(client, userdata, message):
    print("received message: " ,str(message.payload.decode("utf-8")))

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

broker_ip = os.environ['broker_ip']
broker_port = int(os.environ['broker_port'])

client = mqtt.Client(clean_session=True)
client.on_connect=on_connect

client.connect(broker_ip, broker_port) 

client.subscribe("messages")
client.on_message=on_message 

client.loop_forever()

