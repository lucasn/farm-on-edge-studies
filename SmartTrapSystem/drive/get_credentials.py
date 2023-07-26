"""
Run this script to save the Google Drive's credentials to credentials.json
"""
from pydrive.auth import GoogleAuth

try:
    auth = GoogleAuth()
    auth.CommandLineAuth()

except Exception as e:
    print(e)