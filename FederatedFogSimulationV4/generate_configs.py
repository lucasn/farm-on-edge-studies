
def generate_config(n_fogs, n_clients, auction):
    return 'SIMULATION_TIME=20\n' + \
            f'QUANTITY_CLIENTS={n_clients}\n' + \
            'CLOUD_LATENCY=100\n' + \
            f'QUANTITY_FOGS={n_fogs}\n' + \
            'WARMUP_TIME=1\n' + \
            'MESSAGE_PROCESSING_CPU_THRESHOLD=75\n' + \
            'PROCESS_MESSAGE_LEADING_ZEROS=3\n' + \
            'PROCESS_MESSAGE_FUNCTION_REPEAT=7\n' + \
            f'ACTIVATE_AUCTION={auction}\n'

n_configs = int(input('Número de configurações: '))
n_reps = int(input('Número de repetições: '))

with open('./run_configs.txt', 'w') as out:
    for i in range(n_configs):
        n_fogs = int(input(f'Config {i + 1} - Quantidade de fogs: '))
        n_clients = int(input(f'Config {i + 1} - Quantidade de clientes: '))
        for j in range(n_reps):
            out.write(generate_config(n_fogs, n_clients, 1))
            out.write('\n')
            out.write(generate_config(n_fogs, n_clients, 0))
            if i != n_configs - 1 or j != n_reps - 1:
                out.write('\n')