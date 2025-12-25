from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def upload_to_drive(file_path):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    drive = GoogleDrive(gauth)

    f = drive.Createfile({'title': file_path.split("/")[-1]})
    f.SetContentFile(file_path)
    f.upload()
