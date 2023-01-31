from subprocess import Popen, PIPE
from socket import gethostbyname

def ping(hostname):
    p = Popen(['ping', '-c', '1', gethostbyname(hostname)], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    output = p.stdout.read().decode('ascii')

    ping_info = output.split('\n')[1].split(' ')
    for info in ping_info:
        if info.find('time') != -1:
            return info[5:]
    
    raise Exception('Cannot retrieve ping')