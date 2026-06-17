import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import datetime
import config
from sheets import SheetsDB
from attendance import AttendanceEngine, STATUS_UNCHECKED, STATUS_PRESENT, STATUS_LATE, calc_fine, calc_minutes_late

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

db = SheetsDB()
engine = AttendanceEngine()


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


# ── 인증 ──────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == config.ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='비밀번호가 틀렸습니다.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── 대시보드 ──────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    meetings = db.get_meetings()
    meetings = list(reversed(meetings))
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('dashboard.html', meetings=meetings, today=today)


# ── 모임 생성 ─────────────────────────────────────────────
@app.route('/meeting/new', methods=['POST'])
@login_required
def new_meeting():
    name = request.form.get('name', '').strip()
    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    start_time = request.form.get('start_time', '')
    if not name:
        return redirect(url_for('dashboard'))
    meeting_id = db.create_meeting(name, date_str, start_time)
    return redirect(url_for('attend', meeting_id=meeting_id))


# ── 모임 삭제 ─────────────────────────────────────────────
@app.route('/meeting/<meeting_id>/delete', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    db.delete_meeting(meeting_id)
    return redirect(url_for('dashboard'))


# ── 출결 체크 페이지 (부원용 QR 접속) ────────────────────
@app.route('/attend/<meeting_id>')
def attend(meeting_id):
    members = db.get_members()
    attendance = db.get_attendance_for_meeting(meeting_id)
    att_map = {r['이름']: r for r in attendance}
    meeting = db.get_meeting(meeting_id) or {'모임명': '알 수 없음', '날짜': '', '시작시간': ''}
    start_time = meeting.get('시작시간', '')

    member_list = []
    for m in members:
        name = m['이름']
        rec = att_map.get(name, {})
        status = rec.get('상태', STATUS_UNCHECKED)
        phone4 = str(m.get('전화번호 뒤 4자리', '') or '')
        fine = 0
        if status == STATUS_LATE:
            mins = calc_minutes_late(start_time, rec.get('체크시간', ''))
            fine = calc_fine(mins)
        member_list.append({'name': name, 'status': status, 'phone4': phone4, 'fine': fine})

    return render_template('attend.html',
                           members=member_list,
                           meeting_id=meeting_id,
                           meeting=meeting,
                           start_time=start_time)


# ── 출석 확정 API (부원 자가 체크인) ─────────────────────
@app.route('/api/attend', methods=['POST'])
def api_attend():
    data = request.get_json(silent=True) or {}
    meeting_id = data.get('meeting_id')
    member_name = data.get('member_name')
    if not meeting_id or not member_name:
        return jsonify({'error': '필수 값 누락'}), 400

    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': '존재하지 않는 모임'}), 404

    now = datetime.now()
    now_str = now.strftime('%H:%M')
    start_time = meeting.get('시작시간', '')
    mins_late = calc_minutes_late(start_time, now_str)

    status = STATUS_LATE if mins_late > 0 else STATUS_PRESENT
    fine = calc_fine(mins_late) if mins_late > 0 else 0

    db.set_attendance(meeting_id, meeting['날짜'], member_name, status)
    return jsonify({'status': status, 'check_time': now_str, 'fine': fine, 'minutes_late': mins_late})


# ── 출석 취소 API ─────────────────────────────────────────
@app.route('/api/cancel', methods=['POST'])
def api_cancel():
    data = request.get_json(silent=True) or {}
    meeting_id = data.get('meeting_id')
    member_name = data.get('member_name')
    if not meeting_id or not member_name:
        return jsonify({'error': '필수 값 누락'}), 400

    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': '존재하지 않는 모임'}), 404

    db.set_attendance(meeting_id, meeting['날짜'], member_name, STATUS_UNCHECKED)
    return jsonify({'status': STATUS_UNCHECKED})


# ── 출결 토글 API (관리자용) ──────────────────────────────
@app.route('/api/toggle', methods=['POST'])
def toggle():
    data = request.get_json(silent=True) or {}
    meeting_id = data.get('meeting_id')
    member_name = data.get('member_name')
    current_status = data.get('current_status', STATUS_UNCHECKED)
    if not meeting_id or not member_name:
        return jsonify({'error': '필수 값 누락'}), 400

    new_status = engine.next_status(current_status)
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': '존재하지 않는 모임'}), 404

    db.set_attendance(meeting_id, meeting['날짜'], member_name, new_status)
    return jsonify({'status': new_status})


# ── 통계 ──────────────────────────────────────────────────
@app.route('/stats')
@login_required
def stats():
    members = db.get_members()
    all_records = db.get_all_attendance()
    meetings = db.get_meetings()
    meetings_map = {str(m['모임ID']): m for m in meetings}
    summaries = engine.all_summaries(members, all_records, meetings_map)
    return render_template('stats.html', summaries=summaries, total_meetings=len(meetings))


if __name__ == '__main__':
    use_ngrok = os.getenv('USE_NGROK', '').lower() == 'true'
    if use_ngrok:
        from pyngrok import ngrok
        public_url = ngrok.connect(5000)
        print(f'\n단체톡방에 이 링크 공유: {public_url}\n')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
