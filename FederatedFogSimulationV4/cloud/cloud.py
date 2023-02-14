import paho.mqtt.client as mqtt
from json import loads, dumps
from socket import gethostbyname

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
    print(f'Mensagem recebida: {loads(message.payload)}')
    client.publish('client', message.payload)

    data_report_message = {
        'id': 0,
        'data': 'MESSAGE_RECEIVED',
        'type': 'CLOUD'
    }

    client.publish('data', dumps(data_report_message))

if __name__ == '__main__':
    main()