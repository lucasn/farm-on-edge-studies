import os
from datetime import datetime
from picamera import PiCamera
from time import sleep
from subprocess import Popen, PIPE
from urllib import request

from drive.DriveClient import DriveClient

CAMERA_RESOLUTION = (1280, 720)
CAPTURE_FORMAT = 'jpeg'
CAPTURE_PERIOD = 15

dir_path = os.path.dirname(os.path.realpath(__file__))
local_dir = f'{dir_path}/images'
usb_mount_dir = f'{dir_path}/usb'
usb_images_dir = f'{usb_mount_dir}/images'
logs_path = f'{dir_path}/logs.txt'

upload_dir = 'Fotos Armadilhas'

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

        # Uploading images to Google Drive if internet avaliable
        if is_connected_to_internet():
            upload_to_drive()
        
        # Mounting the USB drive if exists and copying the images from the images folder
        else:
            mount_and_copy()

        print('Pictures saved succesfully')
        sleep(CAPTURE_PERIOD - 5)
        print('Taking picture and saving files, do not remove storage')
        sleep(5)

def upload_to_drive():
    try:
        drive = DriveClient()

    except Exception as e:
        write_log('Error while connecting to Drive', 'ERROR')
        write_log(e, 'ERROR')
    
    images = os.listdir(local_dir)

    for image in images:
        image_path = f'{local_dir}/{image}'
        try:
            drive.upload(upload_dir, image, image_path)
            os.remove(image_path)

        except Exception as e:
            write_log('Error while uploading images from local directory', 'ERROR')
            write_log(e, 'ERROR')


    if mount() and os.path.exists(usb_images_dir):
        images = os.listdir(usb_images_dir)

        for image in images:
            image_path = f'{usb_images_dir}/{image}'
            try:
                drive.upload(upload_dir, image, image_path)
                process = Popen(['sudo', 'rm', image_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                _, stderr = process.communicate()

                if stderr:
                    raise Exception(stderr.decode('utf-8'))
                
            except Exception as e:
                write_log('Error while uploading images from USB drive', 'ERROR')
                write_log(e, 'ERROR')
        
        umount()


def mount_and_copy():
    if mount():

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

        umount()


def mount() -> bool:
    process = Popen(['sudo', 'fdisk', '-l'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(b'pi\n')

    if stderr:
        write_log(f'Error while running fdisk', 'ERROR')
        write_log(stderr.decode('utf-8'), 'ERROR')
        return False

    process = Popen(['grep', '/dev/sd'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(stdout)

    if stderr:
        write_log(f'Error while running grep', 'ERROR')
        write_log(stderr.decode('utf-8'), 'ERROR')
        return False

    if stdout:
        stdout_line = stdout.decode('utf-8').split()
        disk = stdout_line[1][:-1]
    
        process = Popen(['sudo', 'mount', disk, usb_mount_dir], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            write_log(f'Error while running mount', 'ERROR')
            write_log(stderr.decode('utf-8'), 'ERROR')
            return False
        
        return True
    
    return False
        

def umount():
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

def is_connected_to_internet() -> bool:
    try:
        request.urlopen('http://www.google.com/', timeout=1)
        return True
    except:
        return False

if __name__=="__main__":
    main()
