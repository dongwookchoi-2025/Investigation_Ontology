"""항공사고 온톨로지 연구 진행상황판 (Streamlit)

- dashboard.html : 진행상황판 본문 (DATA 블록만 고치면 됨)
- manuscript/    : 논문 초안 파일(hwp, pdf 등). 이 폴더에 넣은 파일은 자동으로 다운로드 버튼이 생김
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).parent
MANUSCRIPT_DIR = BASE / "manuscript"
MIME = {
    ".pdf": "application/pdf",
    ".hwp": "application/x-hwp",
    ".hwpx": "application/hwp+zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

st.set_page_config(page_title="항공사고 온톨로지 공정판", page_icon="✈️", layout="wide")
st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:0;max-width:1300px}"
    "header[data-testid='stHeader']{display:none}</style>",
    unsafe_allow_html=True,
)

# ---- 논문 초안 다운로드 ------------------------------------------------------
files = sorted(p for p in MANUSCRIPT_DIR.glob("*") if p.is_file() and p.suffix.lower() in MIME) \
    if MANUSCRIPT_DIR.exists() else []

with st.container(border=True):
    st.markdown("**📄 논문 초안 다운로드** · 항공경영학회 투고본")
    if files:
        cols = st.columns(len(files))
        for col, f in zip(cols, files):
            with col:
                st.download_button(
                    label=f"{f.suffix.upper().lstrip('.')} 다운로드",
                    data=f.read_bytes(),
                    file_name=f.name,
                    mime=MIME[f.suffix.lower()],
                    use_container_width=True,
                    key=f"dl-{f.name}",
                )
                st.caption(f"{f.name} · {f.stat().st_size/1024/1024:.1f} MB")
    else:
        st.caption("manuscript 폴더에 원고 파일이 아직 없습니다.")

# ---- 진행상황판 --------------------------------------------------------------
html = (BASE / "dashboard.html").read_text(encoding="utf-8")
components.html(html, height=6000, scrolling=True)
