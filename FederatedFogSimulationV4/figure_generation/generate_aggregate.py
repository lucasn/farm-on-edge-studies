from utils import open_results

def main():
    reps = int(input('Quantidade de repetições: '))
    f = open('aggregate_input.txt', 'r')
    
    
    for _ in range(reps):
        rep_path = f.readline().replace('\n', '')
        rep_data = open_results(rep_path)
    

if __name__ == '__main__':
    main()