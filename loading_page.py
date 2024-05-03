import streamlit as st
st.set_page_config(page_title="Butler", page_icon='images/butler.png', layout="wide", initial_sidebar_state="collapsed", menu_items=None)
from home_page import nav_page
import html

col1, col2, col3 = st.columns(3)
with col2:
    if 'loading_statement' not in st.session_state:
        st.session_state.loading_statement = 'Building your Custom Dashboard...'
    if 'load_percent' not in st.session_state:
        st.session_state.load_percent = 0
    writing = st.empty()
    writing.subheader(st.session_state.loading_statement)
    loader = st.empty()
    loader.progress(st.session_state.load_percent)

    if st.session_state.load_percent > .99:
        nav_page('')

