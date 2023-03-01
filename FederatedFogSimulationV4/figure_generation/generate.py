from utils import open_results
from figure_generator import FigureGenerator


def main():
    is_both = input("Gerar gráficos com leilão e sem leilão: [S/N] ").lower()

    if is_both == 's':
        pass
    elif is_both == 'n':
        results_path = input("Diretório de resultados: ")
        data = open_results(results_path)
        fig_gen = FigureGenerator(results_path, data)
        fig_gen.generate_all()
    else:
        print('Entrada inválida')
        exit(0)





if __name__ == '__main__':
    main()



















