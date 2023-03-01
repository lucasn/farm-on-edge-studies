import matplotlib.pyplot as plt

class FigureGenerator:
    def __init__(self, results_path, data):
        self.fogs_labels = [f"Fog {i}" for i in data['messages']['fog_label'].to_list()]
        self.fogs_labels[0] = 'Cloud'

        self.results_path = results_path
        self.data = data

    
    def generate_all(self):
        self.generate_received_messages()
        self.generate_direct_messages()
        self.generate_redirect_messages()
        self.generate_cpu_usage()
        self.generate_memory_usage()
        self.generate_response_time()


    def generate_received_messages(self):
        messages_df = self.data['messages']
        env = self.data['env']


        fig = plt.figure()
        plt.bar(self.fogs_labels, messages_df['received_messages_counter'])
        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")

        fig.savefig(f'{self.results_path}/received_messages.png')


    def generate_direct_messages(self):
        messages_df = self.data['messages']
        env = self.data['env']


        max_height = max(messages_df['received_messages_counter'])
        fig = plt.figure()
        plt.bar(self.fogs_labels[1:], messages_df['direct_messages_counter'][1:])
        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")
        plt.ylim(0, max_height)

        fig.savefig(f'{self.results_path}/direct_messages.png')


    def generate_redirect_messages(self):
        messages_df = self.data['messages']
        env = self.data['env']


        max_height = max(messages_df['received_messages_counter'])
        fig = plt.figure()
        plt.bar(self.fogs_labels[1:], messages_df['redirect_messages_counter'][1:])
        plt.ylim(0, max_height)
        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")

        fig.savefig(f'{self.results_path}/redirect_messages.png')


    def generate_cpu_usage(self):
        cpu_df = self.data['cpu']
        env = self.data['env']

        fig = plt.figure()
        for i in range(env['QUANTITY_FOGS']):
            plt.plot(cpu_df['time_reference'], cpu_df[f'Fog {i+1}'])

        plt.ylim(0, 100)
        plt.hlines(env['MESSAGE_PROCESSING_CPU_THRESHOLD'], 0, env['SIMULATION_TIME'], linestyles='dashed', colors='#000000')
        plt.legend(self.fogs_labels[1:])
        plt.xlabel("Tempo na simulação (s)")

        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")

        fig.savefig(f'{self.results_path}/cpu_usage.png')


    def generate_memory_usage(self):
        memory_df = self.data['memory']
        env = self.data['env']
        
        fig = plt.figure()
        for i in range(env['QUANTITY_FOGS']):
            plt.plot(memory_df['time_reference'], memory_df[f'Fog {i+1}'])
        plt.ylim(0, 10)
        plt.legend(self.fogs_labels[1:])
        plt.xlabel("Tempo na simulação (s)")
        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")

        fig.savefig(f'{self.results_path}/mem_usage.png')


    def generate_response_time(self):
        response_time_df = self.data['response_time']
        env = self.data['env']


        fig = plt.figure()
        plt.scatter(response_time_df['instant'], response_time_df['response_time'])
        plt.xlabel("Tempo na simulação (s)")
        if env['ACTIVATE_AUCTION']:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes com leilão")
        else:
            plt.title(f"{env['QUANTITY_FOGS']} fogs e {env['QUANTITY_CLIENTS']} clientes sem leilão")

        fig.savefig(f'{self.results_path}/response_time.png')