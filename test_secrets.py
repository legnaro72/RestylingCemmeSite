import streamlit as st
import os

try:
    val = st.secrets.get("MISSING_KEY", "fallback")
    print("Secrets fallback:", val)
except Exception as e:
    print("Exception:", e)
