from utils import open_results, calculate_confidence_interval
from json import dumps
import numpy as np
import matplotlib.pyplot as plt

def main():
    number_of_reps = int(input('Quantidade de repetições: '))
    number_of_configs = int(input('Quantidade de configurações: '))
    filename = input('Nome da figura: ')

    f = open('aggregate_input.txt', 'r')
    
    configs = []
    for _ in range(number_of_configs):
        config = read_repetitions(f, number_of_reps)
        configs.append(config)

    for config in configs:
        config['with_auction_response_time_mean'] = []
        config['without_auction_response_time_mean'] = []

        for data in config['with_auction_data']:
            config['with_auction_response_time_mean'].append(data['response_time'].mean()['response_time'])

        for data in config['without_auction_data']:
            config['without_auction_response_time_mean'].append(data['response_time'].mean()['response_time'])

    
    for config in configs:
        config['with_auction_response_time_confidence_interval'] = calculate_confidence_interval(
            sample=config['with_auction_response_time_mean'],
            confidence_level=0.95
        )
        config['without_auction_response_time_confidence_interval'] = calculate_confidence_interval(
            sample=config['without_auction_response_time_mean'],
            confidence_level=0.95
        )

    debug_conf_interval = {
        'auction_mean': config['with_auction_response_time_mean'],
        'no_auction_mean': config['without_auction_response_time_mean'],
        'auction_conf_interval': config['with_auction_response_time_confidence_interval'],
        'no_auction_conf_interval': config['without_auction_response_time_confidence_interval']
    }

    debug_conf_interval = dumps(debug_conf_interval)
    with open('debug_conf_interval.json', 'w') as f:
        f.write(debug_conf_interval)
    
    
    y_with_auction = []
    y_without_auction = []
    for config in configs:
        y_with_auction.append((config['with_auction_response_time_confidence_interval'][0] + config['with_auction_response_time_confidence_interval'][1])/2)
        y_without_auction.append((config['without_auction_response_time_confidence_interval'][0] + config['without_auction_response_time_confidence_interval'][1])/2)

    barwidth = 0.2
    fig = plt.subplots(figsize =(12, 8))

    confidence_interval_with_auction = [config['with_auction_response_time_confidence_interval'][1] - y for config, y in zip(configs, y_with_auction)]
    confidence_interval_without_auction = [config['without_auction_response_time_confidence_interval'][1] - y for config, y in zip(configs, y_without_auction)]

    indice = np.arange(len(y_with_auction))
    x1 = [x - barwidth for x in indice]
    x2 = [x + barwidth for x in indice]

    plt.bar(
        x1, 
        y_with_auction, 
        color='r', 
        width=1.5*barwidth, 
        label='Com leilão',
        edgecolor='black',
        capsize=10,
        yerr=confidence_interval_with_auction
    )
    plt.bar(
        x2, 
        y_without_auction, 
        color='b', 
        width=1.5*barwidth, 
        label='Sem leilão',
        edgecolor='black',
        capsize=10,
        yerr=confidence_interval_without_auction
    )

    plt.xlabel('Configuração do experimento')
    plt.ylabel('Tempo de Resposta Médio (s)')
    plt.xticks(
        [r for r in range(len(y_with_auction))],
        [f'{config["QUANTITY_FOGS"]} fogs / {config["QUANTITY_CLIENTS"]} clientes' for config in configs]
    )

    plt.legend()
    plt.savefig(f'aggregate/{filename}.png')



def read_repetitions(file, number_of_reps):
    config = {'with_auction_data': [], 'without_auction_data': []}

    # reading repetitions with auction
    for i in range(number_of_reps):
        experiment_path = file.readline().replace('\n', '')
        data =  open_results(experiment_path)

        if i == 0:
            config['QUANTITY_FOGS'] = data['env']['QUANTITY_FOGS']
            config['QUANTITY_CLIENTS'] = data['env']['QUANTITY_CLIENTS']
            config['with_auction_data'].append(data)
        else:
            config['with_auction_data'].append(data)
            assert config['QUANTITY_FOGS'] == data['env']['QUANTITY_FOGS'], "Configuration between repetitions doesn't match"
            assert config['QUANTITY_CLIENTS'] == data['env']['QUANTITY_CLIENTS'], "Configuration between repetitions doesn't match"

    #reading repetitions without auction 
    for i in range(number_of_reps):
        experiment_path = file.readline().replace('\n', '')
        data =  open_results(experiment_path)

        if i == 0:
            config['QUANTITY_FOGS'] = data['env']['QUANTITY_FOGS']
            config['QUANTITY_CLIENTS'] = data['env']['QUANTITY_CLIENTS']
            config['without_auction_data'].append(data)
        else:
            config['without_auction_data'].append(data)
            assert config['QUANTITY_FOGS'] == data['env']['QUANTITY_FOGS'], "Configuration between repetitions doesn't match"
            assert config['QUANTITY_CLIENTS'] == data['env']['QUANTITY_CLIENTS'], "Configuration between repetitions doesn't match"

    return config


if __name__ == '__main__':
    main()