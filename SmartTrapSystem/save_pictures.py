import os
from datetime import datetime
from picamera import PiCamera
from time import sleep
from subprocess import Popen, PIPE

CAMERA_RESOLUTION = (1280, 720)
CAPTURE_FORMAT = 'jpeg'
CAPTURE_PERIOD = 15

local_dir = './images'
usb_mount_dir = './usb'
logs_path = './logs.txt'

def main():
    write_log('Starting script...')
    camera = PiCamera(resolution=CAMERA_RESOLUTION)

    while True:
        if not os.path.exists(local_dir):
            os.mkdir(local_dir)

        timestamp = datetime.now()
        filename = f'{timestamp.strftime("%d-%m-%Y@%H_%M_%S") }.jpeg'
        file_path = f'{ local_dir }/{ filename }'

        try:
            # Taking picture
            camera.capture(file_path, format=CAPTURE_FORMAT)
        except Exception as e:
            write_log(e, 'ERROR')

        mount_and_copy()

        print('Pictures saved succesfully')
        sleep(CAPTURE_PERIOD - 5)
        print('Taking picture and saving files, do not remove storage')
        sleep(5)


def mount_and_copy():
    process = Popen(['sudo', 'fdisk', '-l'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(b'pi\n')

    if stderr:
        write_log(f'Error while running fdisk', 'ERROR')
        write_log(stderr.decode('utf-8'), 'ERROR')
        return

    process = Popen(['grep', '/dev/sd'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(stdout)

    if stderr:
        write_log(f'Error while running grep', 'ERROR')
        write_log(stderr.decode('utf-8'), 'ERROR')
        return

    if stdout:
        stdout_line = stdout.decode('utf-8').split()
        disk = stdout_line[1][:-1]
    
        process = Popen(['sudo', 'mount', disk, usb_mount_dir], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            write_log(f'Error while running mount', 'ERROR')
            write_log(stderr.decode('utf-8'), 'ERROR')
            return

        if not os.path.exists(usb_mount_dir + '/images/'):
            process = Popen(['sudo', 'mkdir', usb_mount_dir + '/images'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            if stderr:
                write_log(f'Error while running mkdir', 'ERROR')
                write_log(stderr.decode('utf-8'), 'ERROR')

        images = os.listdir(local_dir)

        for image in images:
            process = Popen(['sudo', 'mv', local_dir + f'/{image}', usb_mount_dir + '/images/'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            if stderr:
                write_log(f'Error while running mv', 'ERROR')
                write_log(stderr.decode('utf-8'), 'ERROR')

        process = Popen(['sudo', 'umount', usb_mount_dir], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            write_log(f'Error while running umount', 'ERROR')
            write_log(stderr.decode('utf-8'), 'ERROR')


def write_log(message, type='INFO'):
    with open(logs_path, 'a') as f:
        timestamp = datetime.now()
        log_message = f'{timestamp.strftime("%d-%m-%Y@%H_%M_%S")} [{type}] - {message}\n'
        f.write(log_message)


def get_save_dir():
    if os.path.ismount('./usb'):
        save_dir = './usb/images'
            
    else:
        save_dir = './images'
    
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    
    return save_dir


if __name__=="__main__":
    main()