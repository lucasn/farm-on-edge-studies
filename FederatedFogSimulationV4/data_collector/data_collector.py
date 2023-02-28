from socket import gethostbyname
from datetime import datetime, timedelta
from threading import Timer, Thread
from json import loads, dump
import os
from time import sleep

import pandas as pd
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import docker


QUANTITY_FOGS = int(os.environ['QUANTITY_FOGS'])
QUANTITY_CLIENTS = int(os.environ['QUANTITY_CLIENTS'])
MESSAGE_PROCESSING_CPU_THRESHOLD = int(os.environ['MESSAGE_PROCESSING_CPU_THRESHOLD'])
SIMULATION_TIME = int(os.environ['SIMULATION_TIME'])
WARMUP_TIME = float(os.environ['WARMUP_TIME'])
ACTIVATE_AUCTION = bool(int(os.environ['ACTIVATE_AUCTION']))
CLOUD_LATENCY = int(os.environ['CLOUD_LATENCY'])
PROCESS_MESSAGE_LEADING_ZEROS = int(os.environ['PROCESS_MESSAGE_LEADING_ZEROS'])
PROCESS_MESSAGE_FUNCTION_REPEAT = int(os.environ['PROCESS_MESSAGE_FUNCTION_REPEAT'])
WARMUP_TIME = int(os.environ['WARMUP_TIME'])

received_messages_counter = [0 for i in range(QUANTITY_FOGS + 1)]
direct_messages_counter = [0 for i in range(QUANTITY_FOGS + 1)]
redirect_messages_counter = [0 for i in range(QUANTITY_FOGS + 1)]

cpu_usage_from_docker = [[] for i in range(QUANTITY_FOGS + 1)]
mem_usage_from_docker = [[] for i in range(QUANTITY_FOGS + 1)]
docker_time_reference = []

response_time_instant = []
response_time_value = []

simulation_start_timestamp = None

is_collecting_data = True

docker_is_cgroupv1 = False

def main():
    if ACTIVATE_AUCTION:
        print("[SIMULATION] Simulation with auction")
    else:
        print("[SIMULATION] Simulation without auction")

    sleep(10)
    
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
    streams = [None for i in range(QUANTITY_FOGS)]
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
            try:
                stats = next(stats_stream)

                cpu_percent = retrieve_cpu_usage_from_docker_stats(stats)
                mem_percent = retrieve_memory_usage_from_docker_stats(stats)
                actual_time = retrieve_cpu_usage_timestamp_from_docker_stats(stats)
                
                cpu_usage_from_docker[fog_id + 1].append(cpu_percent)
                mem_usage_from_docker[fog_id + 1].append(mem_percent)
                docker_time_reference.append(
                    (actual_time - time_reference) / timedelta(seconds=1)
                )
            except:
                print('[EXCEPTION] Exception in retrieve_cpu_usage_timestamp_from_docker_stats')

            
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
    actual_time_delta =  datetime_to_timedelta(actual_time)

    return actual_time_delta


def datetime_to_timedelta(timestamp: datetime):
    return timedelta(
        hours=timestamp.hour,
        minutes=timestamp.minute,
        seconds=timestamp.second,
        microseconds=timestamp.microsecond
    )


def sanitize_docker_stats_timestamp(timestamp: str):
    milliseconds_index = timestamp.find('.')
    return datetime.fromisoformat(timestamp[:milliseconds_index + 7])


def on_message(client, userdata, message):
    if is_collecting_data:
        parsed_message = loads(message.payload)
        
        if parsed_message['data'] == 'MESSAGE_RECEIVED':
            received_messages_counter[parsed_message['id']] += 1

            if parsed_message['type'] == 'DIRECT':
                direct_messages_counter[parsed_message['id']] += 1

            elif parsed_message['type'] == 'REDIRECT':
                redirect_messages_counter[parsed_message['id']] += 1
        
        elif parsed_message['data'] == 'RESPONSE_TIME':
            response_time_instant.append(parsed_message['timestamp'])
            response_time_value.append(parsed_message['response_time'])


def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'[BROKER] Data collector connected to MQTT broker')
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
    print('[SIMULATION] Starting simulation...')
    client.publish('start')

    simulation_start_timestamp = datetime.now()

    timer = Timer(SIMULATION_TIME, finish_simulation, args=(client,))
    timer.daemon = True
    timer.start()


def finish_simulation(client: mqtt.Client):
    global is_collecting_data

    is_collecting_data = False

    save_data()

    exit(0)

def save_data():
    timestamp = datetime.now()
    with_or_without_auction = 'with auction' if ACTIVATE_AUCTION else 'without auction'
    results_path = f"./results/{QUANTITY_FOGS} fogs and {QUANTITY_CLIENTS} clients {with_or_without_auction} ({SIMULATION_TIME}s)/{timestamp}"
    
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    print("[DATA] Saving data")

    save_messages_data(results_path)
    save_cpu_usage_data(results_path)
    save_mem_usage_data(results_path)
    save_response_time_data(results_path)
    save_enviromment(results_path)

    print("[DATA] Data saved with sucess")


def save_messages_data(results_path: str):
    messages_df = pd.DataFrame()
    messages_df['fog_label'] = [i for i in range(QUANTITY_FOGS+1)] # 0 is for the cloud
    messages_df['received_messages_counter'] = received_messages_counter
    messages_df['direct_messages_counter'] = direct_messages_counter
    messages_df['redirect_messages_counter'] = redirect_messages_counter
    messages_df.to_csv(f'{results_path}/messages.csv', index=False)


def save_cpu_usage_data(results_path: str):
    global cpu_usage_from_docker, docker_time_reference
    
    min_list_length = len(docker_time_reference)
    for l in cpu_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    cpu_df = pd.DataFrame()
    cpu_df['time_reference'] = docker_time_reference[:min_list_length]
    for i, cpu_usage in enumerate(cpu_usage_from_docker[1:]):
        cpu_df[f'Fog {i+1}'] = cpu_usage[:min_list_length]
    cpu_df.to_csv(f'{results_path}/cpu.csv', index=False)


def save_mem_usage_data(results_path: str):
    global mem_usage_from_docker, docker_time_reference

    min_list_length = len(docker_time_reference)
    for l in cpu_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    memory_df = pd.DataFrame()
    memory_df['time_reference'] = docker_time_reference[:min_list_length]
    for i, mem_usage in enumerate(mem_usage_from_docker[1:]):
        memory_df[f'Fog {i+1}'] = mem_usage[:min_list_length]
    memory_df.to_csv(f'{results_path}/memory.csv', index=False)


def save_response_time_data(results_path: str):
    global simulation_start_timestamp, response_time_value
    reference_time =  datetime_to_timedelta(simulation_start_timestamp)
    converted_time = []
    for timestamp in response_time_instant:
        object_timestamp = datetime.fromisoformat(timestamp)
        delta_timestamp =  datetime_to_timedelta(object_timestamp)
        converted_time.append((delta_timestamp - reference_time) / timedelta(seconds=1))

    response_time_df = pd.DataFrame()
    response_time_df['instant'] = converted_time
    response_time_df['response_time'] = response_time_value
    response_time_df.to_csv(f'{results_path}/response_time.csv', index=False)

def save_enviromment(results_path: str):
    env = {
        'QUANTITY_FOGS': QUANTITY_FOGS,
        'QUANTITY_CLIENTS': QUANTITY_CLIENTS,
        'MESSAGE_PROCESSING_CPU_THRESHOLD': MESSAGE_PROCESSING_CPU_THRESHOLD, 
        'SIMULATION_TIME': SIMULATION_TIME,
        'ACTIVATE_AUCTION': int(ACTIVATE_AUCTION),
        'CLOUD_LATENCY': CLOUD_LATENCY,
        'PROCESS_MESSAGE_LEADING_ZEROS': PROCESS_MESSAGE_LEADING_ZEROS,
        'PROCESS_MESSAGE_FUNCTION_REPEAT': PROCESS_MESSAGE_FUNCTION_REPEAT,
        'WARMUP_TIME': WARMUP_TIME
    }

    with open(f'{results_path}/env.json', 'w') as env_file:
        dump(env, env_file, indent=4)


def generate_figures():
    print('[DATA] Generating figures...')

    fogs_labels = ['Cloud']
    for i in range(QUANTITY_FOGS):
        fogs_labels.append(f'Fog {i + 1}')
    
    timestamp = datetime.now()
    with_or_without_auction = 'with auction' if ACTIVATE_AUCTION else 'without auction'
    results_path = f"./results/{QUANTITY_FOGS} fogs and {QUANTITY_CLIENTS} clients {with_or_without_auction} ({SIMULATION_TIME}s)/{timestamp}"
    
    if not os.path.exists(results_path):
        os.makedirs(results_path)
    
    figure_y_limit = max(received_messages_counter) + 10

    for i in range(QUANTITY_FOGS):
        print(f"len(cpu_usage_from_docker[{i+1}] = {len(cpu_usage_from_docker[i+1])}")

    for i in range(QUANTITY_FOGS):
        print(f"len(mem_usage_from_docker[{i+1}] = {len(mem_usage_from_docker[i+1])}")

    print(f"len(docker_time_reference): {len(docker_time_reference)}")
    
    generate_received_messages_figure(fogs_labels, results_path, figure_y_limit)
    
    generate_direct_messages_figure(fogs_labels, results_path, figure_y_limit)

    generate_redirect_messages_figure(fogs_labels, results_path, figure_y_limit)

    generate_cpu_usage_figure(results_path)

    generate_mem_usage_figure(results_path)

    generate_response_time_figure(results_path)

    print("[DATA] figures generated with success")
    

def generate_received_messages_figure(fogs_labels, results_path, y_limit):
    fig, ax = plt.subplots()
    ax.bar(fogs_labels, received_messages_counter)
    ax.set_title(f'Number of total messages received')
    ax.set_ylabel('Quantity')
    ax.set_ylim(0, y_limit)
    fig.savefig(f'{results_path}/received_messages.png')


def generate_direct_messages_figure(fogs_labels, results_path, y_limit):
    fig, ax = plt.subplots()
    ax.bar(fogs_labels[1:], direct_messages_counter[1:])
    ax.set_title('Number of direct messages received')
    ax.set_ylabel('Quantity')
    ax.set_ylim(0, y_limit)
    fig.savefig(f'{results_path}/direct_messages.png')


def generate_redirect_messages_figure(fogs_labels, results_path, y_limit):
    fig, ax = plt.subplots()
    ax.bar(fogs_labels[1:], redirect_messages_counter[1:])
    ax.set_title('Number of redirected messages received')
    ax.set_ylabel('Quantity')
    ax.set_ylim(0, y_limit)
    fig.savefig(f'{results_path}/redirect_messages.png')


def generate_cpu_usage_figure(results_path):
    global docker_time_reference, cpu_usage_from_docker
    min_list_length = len(docker_time_reference)
    for l in cpu_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    fig, ax = plt.subplots()
    for i in range(QUANTITY_FOGS):
        plt.plot(docker_time_reference[:min_list_length], cpu_usage_from_docker[i + 1][:min_list_length])
    
    ax.hlines(MESSAGE_PROCESSING_CPU_THRESHOLD, min(docker_time_reference), max(docker_time_reference[:min_list_length]), linestyles='dashed', colors='#000000')
    ax.legend([f'Fog {i + 1}' for i in range(QUANTITY_FOGS)])
    ax.set_ylim([0, 100])
    ax.set_xlabel('Seconds')
    ax.set_ylabel('CPU Usage')
    ax.set_title('CPU Consumption by fog')

    fig.savefig(f'{results_path}/cpu_usage.png')


def generate_mem_usage_figure(results_path):
    global docker_time_reference, mem_usage_from_docker

    min_list_length = len(docker_time_reference)
    for l in mem_usage_from_docker[1:]:
        if len(l) < min_list_length:
            min_list_length = len(l)

    fig, ax = plt.subplots()
    for i in range(QUANTITY_FOGS):
        plt.plot(docker_time_reference[:min_list_length], mem_usage_from_docker[i + 1][:min_list_length])

    ax.legend([f'Fog {i + 1}' for i in range(QUANTITY_FOGS)])
    ax.set_ylim([0, 10])
    ax.set_xlabel('Seconds')
    ax.set_ylabel('Memory Usage')
    ax.set_title('Memory Consumption by fog')
    
    fig.savefig(f'{results_path}/mem_usage.png')


def generate_response_time_figure(results_path):
    global simulation_start_timestamp, response_time_value
    reference_time =  datetime_to_timedelta(simulation_start_timestamp)
    converted_time = []
    for timestamp in response_time_instant:
        object_timestamp = datetime.fromisoformat(timestamp)
        delta_timestamp =  datetime_to_timedelta(object_timestamp)
        converted_time.append((delta_timestamp - reference_time) / timedelta(seconds=1))    

    fig, ax = plt.subplots()
    ax.bar(converted_time, response_time_value)
    ax.set_title('Response Time')
    ax.set_ylabel('Seconds')
    fig.savefig(f'{results_path}/response_time_bar.png')

    fig, ax = plt.subplots()
    ax.plot(converted_time, response_time_value)
    ax.set_title('Response Time')
    ax.set_ylabel('Seconds')
    fig.savefig(f'{results_path}/response_time_line.png')


if __name__ == '__main__':
    main()