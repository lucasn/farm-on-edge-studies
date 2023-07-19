import os
from DriveClient import DriveClient

images_dir = './images'
images = os.listdir(images_dir)

drive = DriveClient()
upload_folder = 'Fotos Armadilhas'

for image in images:
    filename = image
    filepath = f'{images_dir}/{filename}'
    
    try: 
        drive.upload(upload_folder, filename, filepath)

    except Exception as e:
        print(e)
