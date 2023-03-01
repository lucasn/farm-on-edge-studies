import pandas as pd
from json import load
from scipy.stat as st

def open_results(results_path):
    with open(f'{results_path}/env.json', 'r') as f:
        env = load(f)

    messages_df = pd.read_csv(f'{results_path}/messages.csv')
    cpu_df = pd.read_csv(f'{results_path}/cpu.csv')
    memory_df = pd.read_csv(f'{results_path}/memory.csv')
    response_time_df = pd.read_csv(f'{results_path}/response_time.csv')

    return {
        'env': env,
        'messages': messages_df,
        'cpu': cpu_df,
        'memory': memory_df,
        'response_time': response_time_df
    }


def calculate_confidence_interval(sample: list, confidence_level: float):
    if len(sample) < 30:
        return st.t.interval(
            confidence=confidence_level,
            df=len(sample)-1,
            loc=np.mean(sample),
            scale=st.sem(sample)
        )
    else:
        return st.norm.interval(
            confidence=confidence_level,
            loc=np.mean(sample),
            scale=st.sem(sample)
        )