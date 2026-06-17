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
            ws = self.ss.add_worksheet(config.SHEET_MEMBERS, rows=200, cols=3)
            ws.append_row(['이름', '전화번호 뒤 4자리'])
        else:
            ws = self._ws(config.SHEET_MEMBERS)
            headers = ws.row_values(1)
            if '전화번호 뒤 4자리' not in headers:
                ws.update_cell(1, len(headers) + 1, '전화번호 뒤 4자리')

        if config.SHEET_MEETINGS not in existing:
            ws = self.ss.add_worksheet(config.SHEET_MEETINGS, rows=200, cols=4)
            ws.append_row(['모임ID', '날짜', '모임명', '시작시간'])
        else:
            ws = self._ws(config.SHEET_MEETINGS)
            if '시작시간' not in ws.row_values(1):
                ws.update_cell(1, len(ws.row_values(1)) + 1, '시작시간')

    # ── 부원 ──────────────────────────────────────────────
    def get_members(self) -> list:
        return self._ws(config.SHEET_MEMBERS).get_all_records()

    # ── 모임 ──────────────────────────────────────────────
    def create_meeting(self, name: str, date_str: str, start_time: str = '') -> str:
        meeting_id = datetime.now().strftime('%Y%m%d%H%M%S')
        self._ws(config.SHEET_MEETINGS).append_row([meeting_id, date_str, name, start_time])

        # 모임명으로 출결 시트 생성
        existing = {s.title for s in self.ss.worksheets()}
        sheet_name = name if name not in existing else f"{name}_{date_str}"
        ws = self.ss.add_worksheet(sheet_name, rows=200, cols=4)
        ws.append_row(['이름', '전화번호 뒤 4자리', '상태', '체크시간'])

        # 전체 부원 미체크로 선 입력
        members = self.get_members()
        if members:
            rows = [[m['이름'], str(m.get('전화번호 뒤 4자리', '') or ''), '미체크', ''] for m in members]
            ws.append_rows(rows)

        return meeting_id

    def get_meetings(self) -> list:
        return self._ws(config.SHEET_MEETINGS).get_all_records()

    def get_meeting(self, meeting_id: str) -> dict | None:
        meetings = self.get_meetings()
        return next((m for m in meetings if str(m['모임ID']) == str(meeting_id)), None)

    def _meeting_sheet_name(self, meeting: dict) -> str | None:
        """모임 dict에서 실제 시트명 찾기 (모임명 또는 모임명_날짜)"""
        name = meeting['모임명']
        date_str = meeting['날짜']
        existing = {s.title for s in self.ss.worksheets()}
        if name in existing:
            return name
        fallback = f"{name}_{date_str}"
        if fallback in existing:
            return fallback
        return None

    # ── 출결 ──────────────────────────────────────────────
    def set_attendance(self, meeting_id: str, date_str: str, member_name: str, status: str):
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return
        sheet_name = self._meeting_sheet_name(meeting)
        if not sheet_name:
            return

        ws = self._ws(sheet_name)
        rows = ws.get_all_values()
        now = datetime.now().strftime('%H:%M:%S')

        for i, row in enumerate(rows[1:], start=2):
            if row[0] == member_name:
                if status == '미체크':
                    ws.update(f'C{i}:D{i}', [['미체크', '']])
                else:
                    ws.update(f'C{i}:D{i}', [[status, now]])
                return

        # 시트에 없으면 새 행 추가 (이전 모임 구조 호환)
        ws.append_row([member_name, '', status, now if status != '미체크' else ''])

    def get_attendance_for_meeting(self, meeting_id: str) -> list:
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return []
        sheet_name = self._meeting_sheet_name(meeting)
        if not sheet_name:
            return []
        try:
            records = self._ws(sheet_name).get_all_records()
            for r in records:
                r['모임ID'] = meeting_id
            return records
        except gspread.exceptions.WorksheetNotFound:
            return []

    def get_all_attendance(self) -> list:
        meetings = self.get_meetings()
        existing_sheets = {s.title for s in self.ss.worksheets()}
        all_records = []
        for m in meetings:
            name = m['모임명']
            date_str = m['날짜']
            if name in existing_sheets:
                sheet_name = name
            elif f"{name}_{date_str}" in existing_sheets:
                sheet_name = f"{name}_{date_str}"
            else:
                continue
            try:
                records = self._ws(sheet_name).get_all_records()
                for r in records:
                    r['모임ID'] = m['모임ID']
                all_records.extend(records)
            except Exception:
                pass
        return all_records
