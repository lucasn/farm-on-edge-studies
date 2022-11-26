import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    print("received message: " ,str(message.payload.decode("utf-8")))

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

mqttBroker ="192.168.0.8"

client = mqtt.Client('client')
client.on_connect=on_connect

client.connect(mqttBroker) 

client.subscribe("TEMPERATURE")
client.on_message=on_message 

client.loop_forever()

