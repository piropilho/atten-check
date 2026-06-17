const searchInput = document.getElementById('searchInput');
const memberList  = document.getElementById('memberList');
const modal       = document.getElementById('modal');
const rows        = Array.from(memberList.querySelectorAll('.member-row'));

let currentMember = null;

// ── 검색 필터 ──────────────────────────────────────────
searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  rows.forEach(row => {
    row.classList.toggle('hidden', q.length > 0 && !row.dataset.name.includes(q));
  });
});

// ── 이름 행 클릭 ───────────────────────────────────────
rows.forEach(row => {
  row.addEventListener('click', () => {
    currentMember = {
      name:   row.dataset.name,
      phone:  row.dataset.phone,
      status: row.dataset.status,
      el:     row,
    };

    document.getElementById('modalName').textContent  = currentMember.name;
    document.getElementById('modalPhone').textContent = currentMember.phone ? `···${currentMember.phone}` : '';

    const msgEl  = document.getElementById('modalMsg');
    const btnsEl = document.getElementById('modalButtons');

    if (currentMember.status === '미체크') {
      msgEl.textContent = '본인이 맞으시면 출석 버튼을 눌러주세요.';
      btnsEl.innerHTML = `
        <button class="btn btn-outline" onclick="closeModal()">취소</button>
        <button class="btn btn-primary" id="confirmAttendBtn" onclick="confirmAttend()">출석</button>
      `;
    } else {
      msgEl.textContent = `현재 상태: ${currentMember.status}`;
      btnsEl.innerHTML = `
        <button class="btn btn-outline" onclick="closeModal()">닫기</button>
        <button class="btn btn-danger" id="cancelAttendBtn" onclick="confirmCancel()">출석 취소</button>
      `;
    }

    modal.classList.remove('hidden');
  });
});

function closeModal() {
  modal.classList.add('hidden');
  currentMember = null;
}

// ── 출석 확정 ──────────────────────────────────────────
async function confirmAttend() {
  const btn = document.getElementById('confirmAttendBtn');
  btn.disabled = true;
  btn.textContent = '처리 중...';

  try {
    const res = await fetch('/api/attend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_id: MEETING_ID, member_name: currentMember.name }),
    });
    if (!res.ok) throw new Error('서버 오류');
    const data = await res.json();

    currentMember.el.dataset.status = data.status;
    updateRowBadge(currentMember.el, data.status);

    const saved = currentMember.name;
    closeModal();
    showResult(saved, data.status, data.check_time, data.fine);
  } catch (e) {
    alert('오류: ' + e.message);
    btn.disabled = false;
    btn.textContent = '출석';
  }
}

// ── 출석 취소 (이미 처리된 경우) ──────────────────────
async function confirmCancel() {
  const btn = document.getElementById('cancelAttendBtn');
  btn.disabled = true;
  btn.textContent = '처리 중...';

  try {
    const res = await fetch('/api/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_id: MEETING_ID, member_name: currentMember.name }),
    });
    if (!res.ok) throw new Error('서버 오류');

    currentMember.el.dataset.status = '미체크';
    updateRowBadge(currentMember.el, '미체크');
    closeModal();
  } catch (e) {
    alert('오류: ' + e.message);
    btn.disabled = false;
    btn.textContent = '출석 취소';
  }
}

// ── 결과 화면 표시 ─────────────────────────────────────
function showResult(name, status, checkTime, fine) {
  const isLate = status === '지각';
  document.getElementById('resultIcon').textContent   = isLate ? '⚠️' : '✅';
  document.getElementById('resultStatus').textContent = isLate ? '지각' : '출석 완료';
  document.getElementById('resultName').textContent   = name;
  document.getElementById('resultTime').textContent   = checkTime;

  const fineEl = document.getElementById('resultFine');
  if (isLate && fine > 0) {
    fineEl.textContent = `벌금 ${fine.toLocaleString()}원`;
    fineEl.classList.remove('hidden');
  } else {
    fineEl.classList.add('hidden');
  }

  document.getElementById('screenResult').dataset.memberName = name;
  document.getElementById('screenSearch').classList.add('hidden');
  document.getElementById('screenResult').classList.remove('hidden');
}

// ── 다시 선택 (결과 화면에서 취소) ────────────────────
async function undoAttend() {
  const name = document.getElementById('screenResult').dataset.memberName;
  try {
    await fetch('/api/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_id: MEETING_ID, member_name: name }),
    });
  } catch (_) {}

  const row = rows.find(r => r.dataset.name === name);
  if (row) {
    row.dataset.status = '미체크';
    updateRowBadge(row, '미체크');
  }

  document.getElementById('screenResult').classList.add('hidden');
  document.getElementById('screenSearch').classList.remove('hidden');
  searchInput.value = '';
  rows.forEach(r => r.classList.remove('hidden'));
}

// ── 행 뱃지 업데이트 ───────────────────────────────────
function updateRowBadge(row, status) {
  const existing = row.querySelector('.mrow-badge');
  if (existing) existing.remove();
  if (status !== '미체크') {
    const badge = document.createElement('span');
    badge.className = `mrow-badge mrow-badge-${status}`;
    badge.textContent = status;
    row.appendChild(badge);
  }
}

// 모달 배경 클릭 시 닫기
modal.addEventListener('click', e => {
  if (e.target === modal) closeModal();
});
