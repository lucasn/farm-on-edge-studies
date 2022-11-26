import paho.mqtt.client as mqtt
import os

broker_ip = os.environ['broker_ip']
broker1_port, broker2_port = os.environ['broker_ports'].split(' ')

client1 = mqtt.Client(clean_session=True)
client2 = mqtt.Client(clean_session=True)

client1.connect((broker_ip, int(broker1_port)))
client2.connect((broker_ip, int(broker2_port)))

