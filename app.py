"""
항공안전 연구 (연구주제4) — 진행현황 대시보드
KCU 논문스터디 · Streamlit

Data source: Dropbox 공유링크 (raw=1)
  progress.yaml  → PROGRESS_URL
  daily_log.md   → DAILY_LOG_URL

배포: Streamlit Community Cloud
  - GitHub private repo에 이 파일 + requirements.txt 올리기
  - Secrets에 아래 두 URL을 넣거나, 코드에 직접 하드코딩
"""

from __future__ import annotations

import re
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
import streamlit as st
import yaml

# ---------------------------------------------------------------------------
# 설정: Dropbox 공유링크
# ---------------------------------------------------------------------------
# 1) Dropbox에서 progress.yaml, daily_log.md 각각 "링크 복사"
# 2) URL 끝의 ?dl=0 을 ?raw=1 로 바꿔서 아래에 붙여넣기
# 3) 또는 Streamlit secrets.toml 에 저장:
#      PROGRESS_URL = "https://..."
#      DAILY_LOG_URL = "https://..."

PROGRESS_URL = st.secrets.get(
    "PROGRESS_URL",
    "https://www.dropbox.com/scl/.../progress.yaml?raw=1",  # ← 교체
)
DAILY_LOG_URL = st.secrets.get(
    "DAILY_LOG_URL",
    "https://www.dropbox.com/scl/.../daily_log.md?raw=1",   # ← 교체
)

REFRESH_SECONDS = 300  # 5분 캐시. 하루 1회 갱신이라 넉넉히.

STATUS_LABEL = {
    "todo": "대기",
    "in_progress": "진행중",
    "blocked": "블로킹",
    "done": "완료",
}
STATUS_COLOR = {
    "todo": "#9CA3AF",
    "in_progress": "#3B82F6",
    "blocked": "#EF4444",
    "done": "#10B981",
}

# ---------------------------------------------------------------------------
# 데이터 로딩
# ---------------------------------------------------------------------------


def _normalize_dropbox_url(url: str) -> str:
    """Dropbox scl 링크를 직접 다운로드 가능한 형식으로 변환.
    ?raw=1, ?dl=0, ?dl=1 어느 형태로 저장돼 있어도 모두 처리."""
    if "dropbox.com" not in url:
        return url
    # www.dropbox.com → dl.dropboxusercontent.com (raw file streaming)
    url = url.replace("://www.dropbox.com/", "://dl.dropboxusercontent.com/")
    url = url.replace("://dropbox.com/", "://dl.dropboxusercontent.com/")
    # dl=0 → dl=1 (raw=1 은 dl.dropboxusercontent.com에서 불필요하지만 안전상 유지)
    url = url.replace("&dl=0", "&dl=1").replace("?dl=0", "?dl=1")
    return url


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_text(url: str) -> str:
    url = _normalize_dropbox_url(url)
    r = requests.get(url, timeout=15, allow_redirects=True)
    r.raise_for_status()
    return r.text


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def load_progress(url: str) -> dict:
    return yaml.safe_load(fetch_text(url)) or {}


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def load_daily_log(url: str) -> str:
    return fetch_text(url)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="항공안전 연구 진행현황",
    page_icon="✈️",
    layout="wide",
)


def render_header(meta: dict) -> None:
    st.title(f"✈️ {meta.get('project', '항공안전 연구')}")
    st.caption(meta.get("subtitle", ""))
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        st.metric("최근 업데이트", meta.get("updated", "—"))
    with c2:
        st.metric("업데이트한 사람", meta.get("updated_by", "—"))
    with c3:
        team = meta.get("team", [])
        st.metric("팀 인원", f"{len(team)}명")
    if team:
        st.caption("팀: " + " · ".join(team))


def status_badge(status: str) -> str:
    color = STATUS_COLOR.get(status, "#6B7280")
    label = STATUS_LABEL.get(status, status)
    return (
        f'<span style="background:{color};color:white;'
        f'padding:2px 10px;border-radius:12px;font-size:0.8rem">{label}</span>'
    )


def render_milestones(milestones: list[dict]) -> None:
    st.subheader("마일스톤")
    if not milestones:
        st.info("마일스톤이 아직 없습니다.")
        return

    # 진척률 요약
    total = len(milestones)
    done = sum(1 for m in milestones if m.get("status") == "done")
    avg = sum(m.get("progress", 0) for m in milestones) / total if total else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 마일스톤", total)
    c2.metric("완료", f"{done} / {total}")
    c3.metric("평균 진척률", f"{avg:.0f}%")

    st.divider()

    for m in milestones:
        header_cols = st.columns([6, 1, 2, 2])
        with header_cols[0]:
            st.markdown(
                f"**{m.get('id', '')}. {m.get('name', '(이름 없음)')}**  "
                f"{status_badge(m.get('status', 'todo'))}",
                unsafe_allow_html=True,
            )
        with header_cols[1]:
            st.write(f"{m.get('progress', 0)}%")
        with header_cols[2]:
            st.caption(f"담당: {m.get('owner', '—')}")
        with header_cols[3]:
            st.caption(f"기한: {m.get('due', '—')}")
        st.progress(min(100, max(0, int(m.get("progress", 0)))) / 100)
        if m.get("note"):
            st.caption(f"📝 {m['note']}")
        st.write("")


def render_experiments(experiments: list[dict]) -> None:
    st.subheader("실험 결과")
    if not experiments:
        st.info("아직 기록된 실험이 없습니다.")
        return
    df = pd.DataFrame(experiments)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # recall@k 추이 라인차트 (있을 때만)
    metric_cols = [c for c in df.columns if c.startswith("recall_at_") or c in ("f1", "em")]
    if "date" in df.columns and metric_cols:
        st.line_chart(df.set_index("date")[metric_cols])


def render_next_actions(actions: list[dict]) -> None:
    st.subheader("다음 액션 (7일 이내)")
    if not actions:
        st.info("등록된 다음 액션 없음.")
        return
    for a in actions:
        st.markdown(f"- **{a.get('owner', '?')}** — {a.get('action', '')}")


def render_issues(issues: list[dict]) -> None:
    if not issues:
        return
    st.subheader("이슈 / 리스크")
    for i in issues:
        st.warning(f"**{i.get('opened', '')}** ({i.get('owner', '?')}) — {i.get('text', '')}")


def render_daily_log(md: str, limit_days: int = 5) -> None:
    st.subheader("Daily Log")
    # 상위 N개 블록만 (--- 로 구분됨)
    blocks = re.split(r"\n---\n", md.strip())
    # 첫 블록은 헤더, 나머지에서 최근 N개
    body_blocks = blocks[1:] if len(blocks) > 1 else []
    shown = body_blocks[:limit_days]
    for b in shown:
        b = b.strip()
        if not b or b.startswith("<!--"):
            continue
        with st.container(border=True):
            st.markdown(b)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        if st.button("🔄 지금 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption(f"자동 갱신: {REFRESH_SECONDS // 60}분마다")
        st.caption(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.divider()
        st.markdown(
            "**데이터 원본**  \n"
            "Dropbox: `KCU 논문스터디/4. 연구주제4. 항공안전/`  \n"
            "`progress.yaml`, `daily_log.md`"
        )

    try:
        data = load_progress(PROGRESS_URL)
        daily_md = load_daily_log(DAILY_LOG_URL)
    except Exception as e:  # noqa: BLE001
        st.error(f"Dropbox에서 파일을 못 읽었어요: {e}")
        st.info(
            "Dropbox 공유링크 URL이 맞는지, 끝에 `?raw=1`이 붙었는지 확인해주세요.\n"
            "또는 Streamlit secrets의 `PROGRESS_URL`, `DAILY_LOG_URL`을 확인하세요."
        )
        return

    render_header(data.get("meta", {}))
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 진행현황", "🧪 실험 / 이슈", "📔 Daily Log"])

    with tab1:
        render_milestones(data.get("milestones", []))
        st.divider()
        render_next_actions(data.get("next_actions", []))

    with tab2:
        render_experiments(data.get("experiments", []))
        st.divider()
        render_issues(data.get("issues", []))

    with tab3:
        render_daily_log(daily_md)


if __name__ == "__main__":
    main()
