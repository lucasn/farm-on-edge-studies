# Smart Trap System
This is the latest version of the embedded code to capture the images of the insects inside the trap to generate the database for the computer vision model. The system saves the images to an USB drive connected to the Raspberry Pi. If there's not an USB connected, the images are saved in the Raspberry storage and moved to the USB when connected.

## Get the Google Drive credentials
1. Follow this [tutorial](https://d35mpxyw7m7k7g.cloudfront.net/bigdata_1/Get+Authentication+for+Google+Service+API+.pdf) to get your client ID and client secret.
2. Create a `settings.yaml` file following the schema
   ```yaml
   client_config_backend: settings
   client_config:
     client_id: YOUR_CLIENT_ID
     client_secret: YOUR_CLIENTE_SECRET
     auth_uri: https://accounts.google.com/o/oauth2/auth
     token_uri: https://accounts.google.com/o/oauth2/token
     redirect_uri: http://localhost:8080/ 
   save_credentials: True
   save_credentials_backend: file
   save_credentials_file: path/to/SmartTrapSystem/drive/credentials.json
   get_refresh_token: True
   oauth_scope:
     - https://www.googleapis.com/auth/drive
     - https://www.googleapis.com/auth/drive.install
   ```
3. In `drive` directory, run the script `get_credentials.py`, click in the link generated and authenticate with the same Google account of step 1.

After all the steps, the `credentials.json` file is generated.