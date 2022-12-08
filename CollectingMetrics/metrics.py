import socket
from time import perf_counter
import os

def main():
    bandwidth = measure_bandwidth(host='xcal1.vodafone.co.uk', port=80)
    latency = measure_latency('google.com', 80)

    print(f'Largura de banda: {bandwidth:.4f} Mbps')
    print(f'Latência: {latency:.4f} milisegundos')

def measure_latency(host, port):
    response = os.popen(f'ping -c 1 {host}').read()

    # Extraindo RTT da resposta do comando ping
    last_line = response.split('\n')[-2]
    find_equal_symbol = last_line.find('=')
    find_bar_after_equal_symbol =  last_line.find('/', find_equal_symbol)

    return float(last_line[find_equal_symbol + 2:find_bar_after_equal_symbol])/2
    

def measure_bandwidth(host, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    request = b'GET /100MB.zip HTTP/1.1\r\nHost: xcal1.vodafone.co.uk\r\nConnection: close\r\n\r\n'
    sock.sendall(request)

    # Recebendo primeiro byte
    sock.recv(1)
    start = perf_counter()

    # Recebendo o restante dos dados
    amount_bytes = 1
    while True:
        chunk = sock.recv(4096)
        if len(chunk) == 0:
            break
        amount_bytes += len(chunk)

    end = perf_counter()

    sock.close()

    # Calculando largura de banda
    bandwidth = (amount_bytes / (1024 * 1024))/(end - start)

    return bandwidth

if __name__ == '__main__':
    main()