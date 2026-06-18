# 📱 ACRO Check-in
> **Automated Attendance Management Platform for ACRO**
> 
> "부원의 개입은 최소화, 모든 프로세스는 유기적인 자동화"

ACRO Check-in은 투자동아리 ACRO의 매주 반복되는 출결 관리 공수를 최소화하고, 수동 기반의 불안정한 데이터를 정교하게 자산화하기 위해 개발된 **출결 자동화 플랫폼**입니다.

부원은 복잡한 인증 없이 QR 코드 스캔과 클릭 한 번으로 1초 만에 체크인을 완료하며, 운영진은 수동 입력이나 리소스 소모 없이 실시간 대시보드와 자동 DB화를 통해 정산 및 출결을 관리할 수 있습니다.

---

## ✨ Key Features (주요 기능)

1. **간편 체크인**
   - QR 코드 스캔 및 본인 확인 팝업을 통한 간결한 체크인 프로세스
   - 복잡한 가입/로그인 절차 배제 및 오출석 방지 로직 적용

2. **실시간 대시보드 (Real-time Sync)**
   - 부원들의 출석 상태를 웹/모바일 대시보드 화면에 새로고침 없이 실시간 반영
   - 세션 진행 상황 모니터링 편의성 극대화

3. **벌금 자동 산정 & DB화**
   - Python 백엔드 엔진을 통한 아크로 자체 벌금 로직 실시간 연산
   - 정상 출석/지각 부원 판별 및 지각 시간에 비례한 패널티 금액 자동 산정
   - 연산된 모든 최종 출결 로그의 Google Sheets 데이터베이스 실시간 적재

---

## 🛠 System Architecture & Workflow (유기적 워크플로우)

본 플랫폼은 운영진의 리소스를 최소화하고 연속성을 확보하기 위해 다음과 같이 유기적인 선형 구조로 설계되었습니다.

- **Deployment (배포 자동화):** GitHub 레포지토리 push와 동시에 Railway 클라우드로 자동 빌드 및 무중단 배포가 수행됩니다.
- **Calculation (연산 자동화):** Flask 경량 웹서버 위에서 가동되는 Python 엔진이 지각 및 벌금을 실시간으로 오차 없이 가공합니다.
- **Management (관리 자동화):** 운영진에게 가장 익숙한 UI인 Google Sheets API를 연동하여 별도의 데이터베이스 관리 도구 학습 없이 출결 현황을 바로 자산화합니다.

---

## 🚀 Tech Stacks (기술 스택)

- **Backend / Engine:** Python, Flask
- **Database / Storage:** Google Sheets API
- **Deployment / Hosting:** Railway, GitHub Actions
