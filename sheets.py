import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import config

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]


def _get_creds() -> Credentials:
    json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if json_str:
        return Credentials.from_service_account_info(json.loads(json_str), scopes=SCOPES)
    return Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)


class SheetsDB:
    def __init__(self):
        gc = gspread.Client(auth=_get_creds())
        self.ss = gc.open_by_key(config.SPREADSHEET_ID)
        self._ensure_sheets()

    def _ws(self, name: str):
        return self.ss.worksheet(name)

    def _ensure_sheets(self):
        existing = {s.title for s in self.ss.worksheets()}

        if config.SHEET_MEMBERS not in existing:
            ws = self.ss.add_worksheet(config.SHEET_MEMBERS, rows=200, cols=5)
            ws.append_row(['이름', '전화번호 뒤 4자리'])
        else:
            ws = self._ws(config.SHEET_MEMBERS)
            headers = ws.row_values(1)
            if '전화번호 뒤 4자리' not in headers:
                ws.update_cell(1, len(headers) + 1, '전화번호 뒤 4자리')

        if config.SHEET_MEETINGS not in existing:
            ws = self.ss.add_worksheet(config.SHEET_MEETINGS, rows=200, cols=5)
            ws.append_row(['모임ID', '날짜', '모임명', '시작시간'])
        else:
            ws = self._ws(config.SHEET_MEETINGS)
            if '시작시간' not in ws.row_values(1):
                ws.update_cell(1, len(ws.row_values(1)) + 1, '시작시간')

        if config.SHEET_ATTENDANCE not in existing:
            ws = self.ss.add_worksheet(config.SHEET_ATTENDANCE, rows=2000, cols=6)
            ws.append_row(['모임ID', '날짜', '이름', '상태', '체크시간'])

    # ── 부원 ──────────────────────────────────────────────
    def get_members(self) -> list:
        return self._ws(config.SHEET_MEMBERS).get_all_records()

    # ── 모임 ──────────────────────────────────────────────
    def create_meeting(self, name: str, date_str: str, start_time: str = '') -> str:
        meeting_id = datetime.now().strftime('%Y%m%d%H%M%S')
        self._ws(config.SHEET_MEETINGS).append_row([meeting_id, date_str, name, start_time])
        return meeting_id

    def get_meetings(self) -> list:
        return self._ws(config.SHEET_MEETINGS).get_all_records()

    def get_meeting(self, meeting_id: str) -> dict | None:
        meetings = self.get_meetings()
        return next((m for m in meetings if str(m['모임ID']) == str(meeting_id)), None)

    # ── 출결 ──────────────────────────────────────────────
    def set_attendance(self, meeting_id: str, date_str: str, member_name: str, status: str):
        ws = self._ws(config.SHEET_ATTENDANCE)
        rows = ws.get_all_values()
        now = datetime.now().strftime('%H:%M:%S')
        for i, row in enumerate(rows[1:], start=2):
            if str(row[0]) == str(meeting_id) and row[2] == member_name:
                ws.update(f'D{i}:E{i}', [[status, now]])
                return
        ws.append_row([meeting_id, date_str, member_name, status, now])

    def get_attendance_for_meeting(self, meeting_id: str) -> list:
        records = self._ws(config.SHEET_ATTENDANCE).get_all_records()
        return [r for r in records if str(r['모임ID']) == str(meeting_id)]

    def get_all_attendance(self) -> list:
        return self._ws(config.SHEET_ATTENDANCE).get_all_records()
