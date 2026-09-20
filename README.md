# 항공안전 연구 진행현황 대시보드

KCU 논문스터디 · 연구주제4 (항공법령 RAG) 진행현황 공유용 Streamlit 앱.

## 구조
```
progress.yaml   ← Dropbox에 저장, 하루 1회 Claude가 갱신
daily_log.md    ← Dropbox에 저장, 매일 새 블록 append
app.py          ← Streamlit 앱 (이 파일들 읽어서 렌더)
```

## 셋업 (10분)

### 1. Dropbox에 데이터 파일 두 개 올리기
- 위치: `KCU 논문스터디/4. 연구주제4. 항공안전/`
- 파일: `progress.yaml`, `daily_log.md`
- (Claude가 이미 만들어뒀으면 이 단계 스킵)

### 2. 두 파일 각각 공유링크 만들기
- Dropbox 웹에서 파일 우클릭 → "링크 복사"
- URL 끝의 `?dl=0` → `?raw=1` 로 변경
- 예: `https://www.dropbox.com/scl/.../progress.yaml?raw=1`

### 3. GitHub private repo에 이 폴더 올리기
```bash
git init
git add app.py requirements.txt README.md
git commit -m "Initial dashboard"
gh repo create aviation-dashboard --private --push
```

### 4. Streamlit Community Cloud에 배포
- https://share.streamlit.io/ 접속 → New app
- Repo 선택, main file: `app.py`
- **Secrets** 탭에서 아래 붙여넣기:
  ```toml
  PROGRESS_URL = "https://www.dropbox.com/scl/.../progress.yaml?raw=1"
  DAILY_LOG_URL = "https://www.dropbox.com/scl/.../daily_log.md?raw=1"
  ```
- Deploy 클릭 → 몇 분 뒤 링크 나옴 → 팀 3명에게 공유

## 매일 업데이트

Claude에게 자연스럽게 말하면 됩니다:
> "오늘 업데이트: 코퍼스 40% 됐고, RAG BM25 베이스라인 recall@5 = 0.61 나옴,
> Zenodo 계정 만들었어."

Claude가:
1. Dropbox에서 `progress.yaml` 읽음
2. 해당 필드 갱신 + `updated` 날짜 오늘로
3. `daily_log.md` 상단에 오늘 블록 추가
4. Dropbox에 저장

Streamlit은 최대 5분 뒤 자동 반영. 즉시 보려면 사이드바 "🔄 지금 새로고침".

## 로컬 실행
```bash
pip install -r requirements.txt
export PROGRESS_URL="..."
export DAILY_LOG_URL="..."
streamlit run app.py
```
또는 `.streamlit/secrets.toml` 만들어서 넣어도 됨.
