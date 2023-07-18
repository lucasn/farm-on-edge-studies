import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class DriveClient:
    def __init__(self):
        if not os.path.isfile('./settings.yaml'):
            raise Exception("[ERROR] settings.yaml not found")
        
        self.__auth = GoogleAuth()
        if not os.path.isfile('./credentials.json'):
            self.__auth.CommandLineAuth()
        self.__drive = GoogleDrive(self.__auth)

        
    
    def __get_folder_id(self, folder_title):
        folder = self.__drive.ListFile({
            'q': f"mimeType='application/vnd.google-apps.folder' and title='{folder_title}' and trashed=false"
        }).GetList()

        if folder:
            return folder[0]['id']
        
        raise Exception(f"[ERROR] {folder_title} not a directory")


    def upload(self, folder_title: str, filename: str, filepath: str):
        try:
            folder_id = self.__get_folder_id(folder_title)
            new_file_metadata = {
                'parents': [{'id': folder_id}],
                'title': filename
            }

            new_file = self.__drive.CreateFile(new_file_metadata)
            new_file.SetContentFile(filepath)
            new_file.Upload()
        
        except Exception as e:
            raise e