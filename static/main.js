// 벌금 계산: 1분 지각 시 2,000원 + 이후 10분당 1,000원
function calcFine(startTime) {
  if (!startTime) return 0;
  const now = new Date();
  const [sh, sm] = startTime.split(':').map(Number);
  const lateMinutes = (now.getHours() * 60 + now.getMinutes()) - (sh * 60 + sm);
  if (lateMinutes <= 0) return 0;
  return 2000 + Math.floor((lateMinutes - 1) / 10) * 1000;
}

function fineText(fine) {
  return fine > 0 ? fine.toLocaleString() + '원' : '';
}

async function toggleAttendance(card) {
  const name = card.dataset.name;
  const meetingId = card.dataset.meetingId;
  const currentStatus = card.dataset.status;
  const startTime = document.getElementById('memberGrid').dataset.startTime;

  card.classList.add('loading');

  try {
    const res = await fetch('/api/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        meeting_id: meetingId,
        member_name: name,
        current_status: currentStatus,
      }),
    });

    if (!res.ok) throw new Error('서버 오류');
    const { status } = await res.json();

    card.dataset.status = status;
    card.className = `member-card status-${status}`;
    card.querySelector('.member-status').textContent = status;

    const fineEl = card.querySelector('.member-fine');
    if (fineEl) {
      fineEl.textContent = status === '지각' ? fineText(calcFine(startTime)) : '';
    }

    updateCounts();
  } catch (e) {
    alert('저장 실패: ' + e.message);
  } finally {
    card.classList.remove('loading');
  }
}

function updateCounts() {
  const cards = document.querySelectorAll('.member-card');
  const counts = { 출석: 0, 지각: 0, 결석: 0, 미체크: 0 };
  cards.forEach(c => {
    const s = c.dataset.status;
    if (counts[s] !== undefined) counts[s]++;
  });

  document.querySelector('.chip-present').textContent = `출석 ${counts['출석']}`;
  document.querySelector('.chip-late').textContent    = `지각 ${counts['지각']}`;
  document.querySelector('.chip-absent').textContent  = `결석 ${counts['결석']}`;
  document.querySelector('.chip-unchecked').textContent = `미체크 ${counts['미체크']}`;
}
