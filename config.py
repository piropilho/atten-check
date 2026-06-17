import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin1234')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-prod')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

SHEET_MEMBERS = '부원'
SHEET_MEETINGS = '모임'
SHEET_ATTENDANCE = '출결'
