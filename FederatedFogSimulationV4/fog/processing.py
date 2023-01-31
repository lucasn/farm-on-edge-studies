from hashlib import sha256

def to_binary(x):
    return bin(x).replace('0b', '')

def proof_of_work(leading_zeros, string='processing'):
    nonce = 0
    while True:
        to_hash = string + str(to_binary(nonce))
        to_hash = to_hash.encode(encoding = 'utf-8')
        hashed = sha256(to_hash).hexdigest()

        leading_zeros_string = ''.join(str(i) for i in leading_zeros * [0])
        check_leading_zeros = hashed[: leading_zeros]

        if check_leading_zeros == leading_zeros_string:
            return
        
        nonce += 1


def process(leading_zeros, times=1, string='processing'):
    for i in range(times):
        proof_of_work(leading_zeros, string)