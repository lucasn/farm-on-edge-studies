import paho.mqtt.client as mqtt
import os
from time import sleep
from random import randint
from asymmetric_auction import hold_auction

LATENCY_LIMITS = (0, 300)
UPLINK_LIMITS = (0, 300)

def main():
    broker_ip = os.environ['broker_ip']
    brokers_port = os.environ['broker_ports'].split(' ')
    fogs_latency = os.environ['fogs_latency'].split(' ')
    fogs_uplink = os.environ['fogs_uplink'].split(' ')
    fogs_number = int(os.environ['fogs_number'])

    fogs = []

    for port in brokers_port:
        fog = mqtt.Client(clean_session=True)
        fog.on_connect=on_connect
        fog.connect(broker_ip, int(port))
        fogs.append(fog)

    while True:
        # gerando quantidade de requests igual ao número de fogs
        requests = []
        for i in range(len(fogs)):
            requests.append(generate_request(LATENCY_LIMITS, UPLINK_LIMITS))

        benefits = calculate_benefits(requests, fogs_latency, fogs_uplink)

        for i, line in enumerate(benefits):
            for j, value in enumerate(line):
                print(f'Benefício Requisição {i} fog {j}: {value}')

        auction = hold_auction(fogs_number, len(requests), benefits)

        for index_request, index_fog in enumerate(auction):
            fogs[index_fog].publish('requests', requests[index_request][2])
            print(f'Enviando requisição {index_request} para a fog {index_fog}')

        sleep(2)


def calculate_benefits(requests: list, fogs_latency: list, fogs_uplink: list):
    benefits = []
    fogs_number = len(fogs_uplink)

    assert fogs_number == len(fogs_latency)

    for request in requests:
        actual_request_benefits = []
        for fog_index in range(fogs_number):
            latency_benefit = request[0] - int(fogs_latency[fog_index])
            uplink_benefit = int(fogs_uplink[fog_index]) - request[1]
            actual_request_benefits.append(latency_benefit + uplink_benefit)
        benefits.append(actual_request_benefits)

    return adjust_benefits(benefits)


def adjust_benefits(benefits: list):
    min_value = 0
    for line in benefits:
        for value in line:
            if value < min_value:
                min_value = value
    
    if min_value != 0:
        for i, line in enumerate(benefits):
            for j, value in enumerate(line):
                benefits[i][j] += abs(min_value)

    return benefits
        

def generate_request(latency_limits: tuple, uplink_limits: tuple):
    request_latency = randint(latency_limits[0], latency_limits[1])
    request_uplink = randint(uplink_limits[0], uplink_limits[1])
    return (request_latency, request_uplink, f'Latência: {request_latency} - Uplink: {request_uplink}')


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected: {client}")
        else:
            print("Failed to connect, return code %d\n", rc)


if __name__ == '__main__':
    main()