import enum
import cv2
import numpy as np

f = open("t10k-images.idx3-ubyte", 'rb')


magic_number = f.read(4)
number_images = f.read(4)
n_rows = int.from_bytes(f.read(4), byteorder='big')
n_columns = int.from_bytes(f.read(4), byteorder='big')

n_images = 30

byte_image = []
byte_image.append(magic_number)
for i in range(n_images):
    for j in range(1, n_rows*n_columns+1):
        byte = f.read(1)
        byte_image.append(byte)

nf = open(f'image_block_{n_images}', 'wb')

for byte in byte_image:
    nf.write(byte)

nf.close()

f.close()