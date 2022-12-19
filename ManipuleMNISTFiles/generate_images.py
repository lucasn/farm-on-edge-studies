import enum
import cv2
import numpy as np

f = open("t10k-images.idx3-ubyte", 'rb')


magic_number = f.read(4)
number_images = f.read(4)
n_rows = int.from_bytes(f.read(4), byteorder='big')
n_columns = int.from_bytes(f.read(4), byteorder='big')


for i in range(10):
    byte_image = []
    image = []
    byte_image.append(magic_number)
    for j in range(1, n_rows*n_columns+1):
        byte = f.read(1)
        byte_image.append(byte)
        pixel = int.from_bytes(byte, byteorder='big')
        image.append(pixel)

    assert len(image) == n_rows * n_columns

    img = np.ones((28,28,1),np.uint8)

    nf = open(f'image{i}', 'wb')

    for b, byte in enumerate(byte_image):
        nf.write(byte)

    nf.close()

    for p, pixel in enumerate(image):
        row = int(p / 28)
        column = p - (row * 28)
        #print(f'Row {row} - Column {column}')
        img[row][column] = image[p]

    cv2.imwrite(f'./image{i}.png', img)



f.close()