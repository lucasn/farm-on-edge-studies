import paho.mqtt.client as mqtt
import os

def main():
    broker_ip = os.environ['broker_ip']
    broker_port = int(os.environ['broker_port'])

    client = mqtt.Client('fog')
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(broker_ip, broker_port)
    client.subscribe("requests")

    client.loop_forever()


def on_message(client, userdata, message):
    print("request received: " ,str(message.payload.decode("utf-8")))

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()