"""
출결 로직 추상화 레이어
규칙 변경 시 이 파일의 설정값과 메서드만 수정하면 됩니다.
"""

from datetime import datetime

STATUS_PRESENT = '출석'
STATUS_LATE = '지각'
STATUS_ABSENT = '결석'
STATUS_UNCHECKED = '미체크'

TOGGLE_CYCLE = [STATUS_UNCHECKED, STATUS_PRESENT, STATUS_LATE, STATUS_ABSENT]

# ── 규칙 설정 ─────────────────────────────────────────────
LATE_PER_ABSENT = 2          # 지각 N회 = 결석 1회
WARNING_THRESHOLD = 3        # 실질 결석 N회 이상 → 경고
EXPEL_THRESHOLD = 5          # 실질 결석 N회 이상 → 제명 대상

FINE_BASE = 2000             # 지각 기본 벌금 (원)
FINE_PER_10MIN = 1000        # 이후 10분당 추가 벌금 (원)
# ──────────────────────────────────────────────────────────


def calc_fine(minutes_late: int) -> int:
    """지각 벌금 계산. 1분이라도 늦으면 기본 2,000원 + 10분당 1,000원."""
    if minutes_late <= 0:
        return 0
    return FINE_BASE + ((minutes_late - 1) // 10) * FINE_PER_10MIN


def calc_minutes_late(start_time: str, check_time: str) -> int:
    """HH:MM 또는 HH:MM:SS 형식의 두 시간 차이를 분으로 반환."""
    if not start_time or not check_time:
        return 0
    try:
        start = datetime.strptime(start_time[:5], '%H:%M')
        check = datetime.strptime(check_time[:5], '%H:%M')
        diff = int((check - start).total_seconds() / 60)
        return max(0, diff)
    except ValueError:
        return 0


class AttendanceEngine:
    def next_status(self, current: str) -> str:
        """토글 순서: 미체크 → 출석 → 지각 → 결석 → 미체크"""
        idx = TOGGLE_CYCLE.index(current) if current in TOGGLE_CYCLE else 0
        return TOGGLE_CYCLE[(idx + 1) % len(TOGGLE_CYCLE)]

    def effective_absences(self, records: list) -> float:
        """지각 포함한 실질 결석 횟수"""
        absent = sum(1 for r in records if r['상태'] == STATUS_ABSENT)
        late = sum(1 for r in records if r['상태'] == STATUS_LATE)
        return absent + (late // LATE_PER_ABSENT)

    def member_summary(self, name: str, all_records: list, meetings_map: dict) -> dict:
        records = [r for r in all_records if r['이름'] == name]
        present = sum(1 for r in records if r['상태'] == STATUS_PRESENT)
        late = sum(1 for r in records if r['상태'] == STATUS_LATE)
        absent = sum(1 for r in records if r['상태'] == STATUS_ABSENT)
        eff = self.effective_absences(records)

        total_fine = 0
        for r in records:
            if r['상태'] == STATUS_LATE:
                meeting = meetings_map.get(str(r['모임ID']), {})
                mins = calc_minutes_late(meeting.get('시작시간', ''), r.get('체크시간', ''))
                total_fine += calc_fine(mins)

        return {
            'name': name,
            'present': present,
            'late': late,
            'absent': absent,
            'effective_absent': eff,
            'total': len(records),
            'warning': eff >= WARNING_THRESHOLD,
            'expel_risk': eff >= EXPEL_THRESHOLD,
            'total_fine': total_fine,
        }

    def all_summaries(self, members: list, all_records: list, meetings_map: dict) -> list:
        return [self.member_summary(m['이름'], all_records, meetings_map) for m in members]
