from utils import open_results, calculate_confidence_interval

def main():
    number_of_reps = int(input('Quantidade de repetições: '))
    number_of_configs = int(input('Quantidade de configurações: '))

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