# -*- coding: utf-8 -*-
"""
HCSR interactive maps — one Streamlit app, one dropdown, nine maps.

Run locally (from this folder):      streamlit run app.py
Each map also has its own address:  http://localhost:8501/ras-el-bar   (see menu.py)
Embed one map without the dropdown: http://localhost:8501/ras-el-bar?embed=true&menu=off

Needs Streamlit 1.45 or newer (see requirements.txt).
"""
import streamlit as st
from streamlit.errors import StreamlitAPIException

# must be the very first Streamlit command; some Streamlit versions refuse a second call
# on reruns, so a refusal is ignored (the settings from the first run stay in place)
try:
    st.set_page_config(page_title="HCSR Maps", page_icon="🗺️", layout="wide",
                       initial_sidebar_state="collapsed")
except StreamlitAPIException:
    pass

import common as c                      # noqa: E402  (imported after set_page_config on purpose)
from menu import HOME, MAPS, SITE_TITLE  # noqa: E402

st.markdown(c.PAGE_CSS, unsafe_allow_html=True)

home = st.Page(HOME[0], title=HOME[1], icon=HOME[2], default=True)
maps = [st.Page(f, title=t, icon=i, url_path=u) for f, t, i, u, _d in MAPS]
pages = [home] + maps
current = st.navigation(pages, position="hidden")

# count page visits: each map is redrawn from scratch when you come back to it
if st.session_state.get("_page") != current.url_path:
    st.session_state["_page"] = current.url_path
    st.session_state["_page_visit"] = st.session_state.get("_page_visit", 0) + 1

# top dropdown (hidden with ?menu=off, e.g. when one map is embedded in the website)
if st.query_params.get("menu", "on") != "off":
    titles = [f"{p.icon} {p.title}" for p in pages]
    idx = next((i for i, p in enumerate(pages) if p.url_path == current.url_path), 0)
    left, _right = st.columns([2, 3])
    with left:
        chosen = st.selectbox("اختر الخريطة", titles, index=idx, key=f"nav_{current.url_path or 'home'}",
                              label_visibility="collapsed")
    if titles.index(chosen) != idx:
        st.switch_page(pages[titles.index(chosen)])

current.run()
