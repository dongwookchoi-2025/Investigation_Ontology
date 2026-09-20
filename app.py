"""항공사고 온톨로지 연구 진행상황판 (Streamlit)
같은 폴더의 dashboard.html을 그대로 화면에 띄웁니다.
내용을 고치려면 dashboard.html 위쪽의 DATA 블록만 수정해서 GitHub에 다시 올리면 됩니다.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="항공사고 온톨로지 공정판", page_icon="✈️", layout="wide")

# Streamlit 기본 여백을 줄여 대시보드가 화면을 넓게 쓰도록 함
st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:0;max-width:1300px}"
    "header[data-testid='stHeader']{display:none}</style>",
    unsafe_allow_html=True,
)

html = (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")
components.html(html, height=3800, scrolling=True)
