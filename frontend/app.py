"""
Finance Credit Follow-Up Email Agent — Landing Page.
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils.theme import BANKING_THEME

st.set_page_config(
    page_title="Finance Credit Follow-Up Email Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(BANKING_THEME, unsafe_allow_html=True)

st.markdown("""
<style>
.hero-container { text-align: center; padding: 4rem 0 2rem; }
.hero-logo { font-size: 3.5rem; margin-bottom: 0.5rem; }
.hero-title {
    font-size: 2.8rem; font-weight: 800; letter-spacing: -1px;
    background: linear-gradient(135deg, #0F2A4A 0%, #1D4ED8 50%, #3B82F6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem; line-height: 1.2;
}
.hero-subtitle { font-size: 1.15rem; color: #475569 !important; margin-bottom: 2rem; font-weight: 400; }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-logo">🏦</div>
    <div class="hero-title">Finance Credit<br>Follow-Up Email Agent</div>
    <div class="hero-subtitle">
        AI-powered automated email escalation, smart payment tracking,<br>
        and full audit trail for your finance team.
    </div>
</div>
""", unsafe_allow_html=True)
