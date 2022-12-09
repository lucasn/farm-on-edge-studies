import paho.mqtt.client as mqtt
import os
from copy import deepcopy
from random import randint

from asymmetric_auction import hold_auction
from config import BROKER_IP, BROKER_PORT

FOG_ID = int(os.environ['fog_id'])
uplink_table = []
fogs_number = 0

linksets = {}


def main():
    global uplink_table, fogs_number

    print(f'Id da fog atual: {FOG_ID}')

    fogs_number, uplink_table = retrieve_uplinks_mapping(FOG_ID)

    print(f'Número de fogs: {fogs_number}')

    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(BROKER_IP, BROKER_PORT)
    client.subscribe(f'fog_{FOG_ID}')

    client.loop_forever()


def on_message(client, userdata, message):
    global linksets

    linkset_id, message = str(message.payload.decode("utf-8")).split('#')

    print(f'Id do linkset: {linkset_id}')
    print(f'Mensagem: {message}')

    if linkset_id == '0':
        print('Enviando mensagem pra a nuvem')
        client.publish('cloud', message + f'-fog_{FOG_ID}')
        return 

    if linkset_id not in linksets:
        actual_uplink_table = []
        actual_uplink_table.append(deepcopy(uplink_table))
        actual_linkset = []
        i = 0
        while i < 3:
            linkset_fog = hold_auction(fogs_number, 1, actual_uplink_table)[0]
            actual_linkset.append(linkset_fog)
            actual_uplink_table[0][linkset_fog] = 0
            i += 1
        
        print(f'Fogs escolhidas para o linkset: {actual_linkset}')
        
        linksets[linkset_id] = actual_linkset
    
    fog = randint(0, len(linksets[linkset_id]) - 1)

    print(f'Pacote sendo enviado para a fog {linksets[linkset_id][fog]}')

    client.publish(f'fog_{linksets[linkset_id][fog]}', f'0#{message}-fog_{FOG_ID}')



def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Fog {FOG_ID} connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def retrieve_uplinks_mapping(fog_id):
    uplink_file = open('./uplink_table.txt', 'r')
    fogs_number, lines_number = uplink_file.readline().split(' - ')

    fogs_number = int(fogs_number)
    lines_number = int(lines_number)

    uplink_table = []
    for i in range(fogs_number):
        uplink_table.append(0)

    for i in range(lines_number):
        fog1, fog2, uplink = uplink_file.readline().split(' - ')

        if int(fog1) == fog_id:
            uplink_table[int(fog2)] = int(uplink)
        if int(fog2) == fog_id:
            uplink_table[int(fog1)] = int(uplink)

    return fogs_number, uplink_table



if __name__ == '__main__':
    main()