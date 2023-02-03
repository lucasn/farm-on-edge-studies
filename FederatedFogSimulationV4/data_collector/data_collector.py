from socket import gethostbyname
from datetime import datetime, timedelta
from threading import Timer, Thread
from json import loads
import os
from time import sleep
from pprint import PrettyPrinter

import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import docker


QNT_FOGS = int(os.environ['QUANTITY_FOGS'])
SIMULATION_TIME = int(os.environ['SIMULATION_TIME'])
WARMUP_TIME = float(os.environ['WARMUP_TIME'])

received_messages_counter = [0 for i in range(QNT_FOGS + 1)]
direct_messages_counter = [0 for i in range(QNT_FOGS + 1)]
redirect_messages_counter = [0 for i in range(QNT_FOGS + 1)]

cpu_usage = [[] for i in range(QNT_FOGS)]
cpu_usage_from_docker = [[] for i in range(QNT_FOGS + 1)]
cpu_usage_time_reference = []

is_collecting_data = True


def main():
    client = connect_to_broker(gethostbyname('mosquitto'), 1883)

    client.subscribe('data')

    t = Thread(target=collect_cpu_usage_from_docker)
    t.start()

    timer = Timer(WARMUP_TIME, start_simulation, args=(client, ))
    timer.start()
    
    collect_cpu_usage_from_docker()

    client.loop_forever()


def collect_cpu_usage_from_docker():
    docker_client = docker.from_env()

    containers = docker_client.containers.list()
    streams = [None for i in range(QNT_FOGS)]
    for container in containers:
        if container.name.find('simulation-fog') != -1:
            fog_id = int(container.name.split('-')[2])
            streams[fog_id - 1] = container.stats(decode=True)


    for i, stream in enumerate(streams):
        if i == 0:
            Thread(target=collect_container_time_and_cpu_usage, args=(i,stream)).start()
        else:
            Thread(target=collect_container_cpu_usage, args=(i, stream)).start()

            
def collect_container_cpu_usage(fog_id, stats_stream):
    global cpu_usage_from_docker

    next(stats_stream)
    while True:
        if is_collecting_data:
            stats = next(stats_stream)

            cpu_percent = retrieve_cpu_usage_from_docker_stats(stats)

            cpu_usage_from_docker[fog_id + 1].append(cpu_percent)


def retrieve_cpu_usage_from_docker_stats(stats):
    online_cpus = stats['cpu_stats']['online_cpus']
    delta_container = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']

    delta_system = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    cpu_percent = (delta_container / delta_system) * online_cpus * 100
    
    return cpu_percent


def collect_container_time_and_cpu_usage(fog_id, stats_stream):
    global cpu_usage_from_docker, cpu_usage_time_reference

    time_reference = next(stats_stream)['read']
    time_reference = sanitize_docker_stats_timestamp(time_reference)
    time_reference_delta =  timedelta(
                hours=time_reference.hour, 
                minutes=time_reference.minute, 
                seconds=time_reference.second, 
                microseconds=time_reference.microsecond
            )

    while True:
        if is_collecting_data:
            stats = next(stats_stream)

            cpu_percent = retrieve_cpu_usage_from_docker_stats(stats)

            cpu_usage_from_docker[fog_id + 1].append(cpu_percent)

            actual_time = stats['read']
            actual_time = sanitize_docker_stats_timestamp(actual_time)
            actual_time_delta =  timedelta(
                hours=actual_time.hour, 
                minutes=actual_time.minute, 
                seconds=actual_time.second, 
                microseconds=actual_time.microsecond
            )

            # (td / timedelta(milliseconds=1)) converts to milliseconds
            cpu_usage_time_reference.append((actual_time_delta - time_reference_delta) / timedelta(milliseconds=1))


def sanitize_docker_stats_timestamp(timestamp: str):
    milliseconds_index = timestamp.find('.')
    return datetime.fromisoformat(timestamp[:milliseconds_index + 7])


def on_message(client, userdata, message):
    if is_collecting_data:
        parsed_message = loads(message.payload)
        
        if parsed_message['data'] == 'MESSAGE_RECEIVED':
            received_messages_counter[parsed_message['id']] += 1

            if parsed_message['details'] == 'DIRECT':
                direct_messages_counter[parsed_message['id']] += 1
            
            else:
                redirect_messages_counter[parsed_message['id']] += 1

        elif parsed_message['data'] == 'CPU_USAGE':
            cpu_usage[parsed_message['id'] - 1].append(parsed_message['cpu_usage'])


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Data collector connected to MQTT broker')
        else:
            print("Failed to connect, return code %d\n", rc)


def connect_to_broker(host, port):
    client = mqtt.Client(clean_session=True)
    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(host, port)
    return client


def start_simulation(client: mqtt.Client):
    print('Iniciando simulação...')
    client.publish('start')

    timer = Timer(SIMULATION_TIME, finish_simulation, args=(client,))
    timer.daemon = True
    timer.start()


def finish_simulation(client: mqtt.Client):
    global is_collecting_data

    is_collecting_data = False

    generate_figures()

    client.disconnect()


def generate_figures():
    global cpu_usage_from_docker, cpu_usage_time_reference

    print('Generating figures...')

    fogs_labels = ['Cloud']
    for i in range(QNT_FOGS):
        fogs_labels.append(f'Fog {i + 1}')
    
    results_path = './results'
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    timestamp = datetime.now()

    plt.figure()
    plt.bar(fogs_labels, received_messages_counter)
    plt.title('Number of total messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/received_messages - {timestamp}.png')

    plt.figure()
    plt.bar(fogs_labels, direct_messages_counter)
    plt.title('Number of direct messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/direct_messages - {timestamp}.png')

    plt.figure()
    plt.bar(fogs_labels, redirect_messages_counter)
    plt.title('Number of redirected messages received')
    plt.ylabel('Quantity')
    plt.savefig(f'{results_path}/redirect_messages - {timestamp}.png')

    cpu_usage_time_reference = [v / 1000 for v in cpu_usage_time_reference]

    min_list_length = len(cpu_usage_time_reference)
    for l in cpu_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    plt.figure()
    for i in range(QNT_FOGS):
        plt.plot(cpu_usage_time_reference[:min_list_length], cpu_usage_from_docker[i + 1][:min_list_length])
    plt.legend([f'Fog {i + 1}' for i in range(QNT_FOGS)])
    plt.ylim([0, 100])
    plt.xlabel('Seconds')
    plt.ylabel('CPU Usage')
    plt.title('CPU Consumption by fog')
    plt.savefig(f'{results_path}/cpu_usage - {timestamp}.png')

if __name__ == '__main__':
    main()