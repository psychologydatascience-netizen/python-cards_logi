import streamlit as st

st.set_page_config(page_title="Card Trials", layout="centered")

# redirect only once per session
if "did_redirect" not in st.session_state:
    st.session_state.did_redirect = True
    st.switch_page("pages/01_Instructions.py")

st.stop()
