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

cpu_usage_from_docker = [[] for i in range(QNT_FOGS + 1)]
mem_usage_from_docker = [[] for i in range(QNT_FOGS + 1)]
docker_time_reference = []

response_time_instant = []
response_time_value = []

simulation_start_timestamp = None

is_collecting_data = True

docker_is_cgroupv1 = False

def main():
    check_docker_group_version()

    client = connect_to_broker(gethostbyname('mosquitto'), 1883)
    client.subscribe('data')

    t = Thread(target=collect_cpu_usage_from_docker)
    t.start()

    timer = Timer(WARMUP_TIME, start_simulation, args=(client, ))
    timer.start()
    
    collect_cpu_usage_from_docker()

    client.loop_forever()


def check_docker_group_version():
    global docker_is_cgroupv1
    cgroupv2_file_path = '/sys/fs/cgroup/cgroup.controllers'

    if not os.path.exists(cgroupv2_file_path):
        docker_is_cgroupv1 = True


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


def collect_container_time_and_cpu_usage(fog_id, stats_stream):
    global cpu_usage_from_docker, docker_time_reference

    stats = next(stats_stream)
    time_reference = retrieve_cpu_usage_timestamp_from_docker_stats(stats)
    while True:
        if is_collecting_data:
            stats = next(stats_stream)

            cpu_percent = retrieve_cpu_usage_from_docker_stats(stats)
            cpu_usage_from_docker[fog_id + 1].append(cpu_percent)

            mem_percent = retrieve_memory_usage_from_docker_stats(stats)
            mem_usage_from_docker[fog_id + 1].append(mem_percent)

            actual_time = retrieve_cpu_usage_timestamp_from_docker_stats(stats)
            docker_time_reference.append(
                (actual_time - time_reference) / timedelta(seconds=1)
            ) 

            
def collect_container_cpu_usage(fog_id, stats_stream):
    global cpu_usage_from_docker

    next(stats_stream)
    while True:
        if is_collecting_data:
            stats = next(stats_stream)
            
            cpu_percent = retrieve_cpu_usage_from_docker_stats(stats)
            cpu_usage_from_docker[fog_id + 1].append(cpu_percent)

            mem_percent = retrieve_memory_usage_from_docker_stats(stats)
            mem_usage_from_docker[fog_id + 1].append(mem_percent)


def retrieve_memory_usage_from_docker_stats(stats):
    mem_usage = stats['memory_stats']['usage']
    if docker_is_cgroupv1:
        total_inactive_file = stats['memory_stats']['stats']['total_inactive_file']
        if total_inactive_file < mem_usage:
            mem_usage = mem_usage - total_inactive_file
    else:
        inactive_file = stats['memory_stats']['stats']['inactive_file']
        if inactive_file < mem_usage:
            mem_usage = mem_usage - inactive_file
    
    limit = stats['memory_stats']['limit']

    if limit != 0:
        return mem_usage / limit * 100
    else:
        return 0


def retrieve_cpu_usage_from_docker_stats(stats):
    online_cpus = stats['cpu_stats']['online_cpus']
    delta_container = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']

    delta_system = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    cpu_percent = (delta_container / delta_system) * online_cpus * 100
    
    return cpu_percent


def retrieve_cpu_usage_timestamp_from_docker_stats(stats):
    actual_time = stats['read']
    actual_time = sanitize_docker_stats_timestamp(actual_time)
    actual_time_delta =  timedelta(
        hours=actual_time.hour, 
        minutes=actual_time.minute, 
        seconds=actual_time.second, 
        microseconds=actual_time.microsecond
    )

    return actual_time_delta


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

            elif parsed_message['details'] == 'REDIRECT':
                redirect_messages_counter[parsed_message['id']] += 1
        
        elif parsed_message['data'] == 'RESPONSE_TIME':
            response_time_instant.append(parsed_message['timestamp'])
            response_time_value.append(parsed_message['response_time'])


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
    global simulation_start_timestamp
    print('Iniciando simulação...')
    client.publish('start')

    simulation_start_timestamp = datetime.now()

    timer = Timer(SIMULATION_TIME, finish_simulation, args=(client,))
    timer.daemon = True
    timer.start()


def finish_simulation(client: mqtt.Client):
    global is_collecting_data

    is_collecting_data = False

    generate_figures()

    client.disconnect()

    exit(0)


def generate_figures():
    print('Generating figures...')

    fogs_labels = ['Cloud']
    for i in range(QNT_FOGS):
        fogs_labels.append(f'Fog {i + 1}')
    
    results_path = './results'
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    generate_received_messages_figure(fogs_labels, results_path)
    
    generate_direct_messages_figure(fogs_labels, results_path)

    generate_redirect_messages_figure(fogs_labels, results_path)

    generate_cpu_usage_figure(results_path)

    generate_mem_usage_figure(results_path)

    generate_response_time_figure(results_path)
    

def generate_received_messages_figure(fogs_labels, results_path):
    timestamp = datetime.now()

    fig, ax = plt.subplots()
    ax.bar(fogs_labels, received_messages_counter)
    ax.set_title('Number of total messages received')
    ax.set_ylabel('Quantity')
    fig.savefig(f'{results_path}/received_messages - {timestamp}.png')


def generate_direct_messages_figure(fogs_labels, results_path):
    timestamp = datetime.now()

    fig, ax = plt.subplots()
    ax.bar(fogs_labels[1:], direct_messages_counter[1:])
    ax.set_title('Number of direct messages received')
    ax.set_ylabel('Quantity')
    fig.savefig(f'{results_path}/direct_messages - {timestamp}.png')


def generate_redirect_messages_figure(fogs_labels, results_path):
    timestamp = datetime.now()

    fig, ax = plt.subplots()
    ax.bar(fogs_labels[1:], redirect_messages_counter[1:])
    ax.set_title('Number of redirected messages received')
    ax.set_ylabel('Quantity')
    fig.savefig(f'{results_path}/redirect_messages - {timestamp}.png')


def generate_cpu_usage_figure(results_path):
    global docker_time_reference, cpu_usage_from_docker
    min_list_length = len(docker_time_reference)
    for l in cpu_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    fig, ax = plt.subplots()
    for i in range(QNT_FOGS):
        plt.plot(docker_time_reference[:min_list_length], cpu_usage_from_docker[i + 1][:min_list_length])

    ax.legend([f'Fog {i + 1}' for i in range(QNT_FOGS)])
    ax.set_ylim([0, 100])
    ax.set_xlabel('Seconds')
    ax.set_ylabel('CPU Usage')
    ax.set_title('CPU Consumption by fog')

    timestamp = datetime.now()
    fig.savefig(f'{results_path}/cpu_usage - {timestamp}.png')


def generate_mem_usage_figure(results_path):
    global docker_time_reference, mem_usage_from_docker

    print(response_time_value)

    min_list_length = len(docker_time_reference)
    for l in mem_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    fig, ax = plt.subplots()
    for i in range(QNT_FOGS):
        plt.plot(docker_time_reference[:min_list_length], mem_usage_from_docker[i + 1][:min_list_length])

    ax.legend([f'Fog {i + 1}' for i in range(QNT_FOGS)])
    ax.set_ylim([0, 10])
    ax.set_xlabel('Seconds')
    ax.set_ylabel('Memory Usage')
    ax.set_title('Memory Consumption by fog')

    timestamp = datetime.now()
    fig.savefig(f'{results_path}/mem_usage - {timestamp}.png')


def generate_response_time_figure(results_path):
    global simulation_start_timestamp, response_time_value
    reference_time =  timedelta(
        hours=simulation_start_timestamp.hour, 
        minutes=simulation_start_timestamp.minute, 
        seconds=simulation_start_timestamp.second, 
        microseconds=simulation_start_timestamp.microsecond
    )
    converted_time = []
    for timestamp in response_time_instant:
        object_timestamp = datetime.fromisoformat(timestamp)
        delta_timestamp =  timedelta(
            hours=object_timestamp.hour, 
            minutes=object_timestamp.minute, 
            seconds=object_timestamp.second, 
            microseconds=object_timestamp.microsecond
        )
        converted_time.append((delta_timestamp - reference_time) / timedelta(seconds=1))
    
    fig, ax = plt.subplots()
    ax.plot(converted_time, response_time_value)
    ax.set_title('Response Time')
    ax.set_ylabel('Seconds')
    fig.savefig(f'{results_path}/response_time - {timestamp}.png')

    fig, ax = plt.subplots()
    ax.scatter(converted_time, response_time_value)
    ax.set_title('Response Time')
    ax.set_ylabel('Seconds')
    fig.savefig(f'{results_path}/response_time_scatter - {timestamp}.png')

    fig, ax = plt.subplots()
    ax.bar(converted_time, response_time_value)
    ax.set_title('Response Time')
    ax.set_ylabel('Seconds')
    fig.savefig(f'{results_path}/response_time_bar - {timestamp}.png')


if __name__ == '__main__':
    main()