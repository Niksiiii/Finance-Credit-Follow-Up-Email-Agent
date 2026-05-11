"""
Shared banking theme CSS for all Streamlit pages.
White background + navy sidebar + dark readable text.
Overrides ALL Streamlit widget dark-mode styles.
"""

BANKING_THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }

/* ════════════════════════════════════════════
   PAGE BACKGROUNDS
   ════════════════════════════════════════════ */
.stApp,
[data-testid="stAppViewContainer"],
.main, .main .block-container,
section[data-testid="stMainBlockContainer"],
[data-testid="stMainBlockContainer"],
.block-container { background-color: #F8FAFC !important; }

/* ════════════════════════════════════════════
   SIDEBAR — dark navy
   ════════════════════════════════════════════ */
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0F2A4A 0%, #1A365D 100%) !important;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #CBD5E1 !important; }

/* ════════════════════════════════════════════
   HEADINGS
   ════════════════════════════════════════════ */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #0F2A4A !important; }

/* ════════════════════════════════════════════
   BODY TEXT — dark readable
   ════════════════════════════════════════════ */
.main p, .main span, .main div, .main li, .main label,
.main .stMarkdown, .main .stMarkdown p, .main .stMarkdown li,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em { color: #1E293B !important; }

/* Caption text */
.stCaption, small, .stMarkdown small,
[data-testid="stCaptionContainer"] * { color: #475569 !important; }

/* ════════════════════════════════════════════
   METRICS — dark, bold
   ════════════════════════════════════════════ */
[data-testid="stMetricValue"] { color: #0F2A4A !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #334155 !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] { font-weight: 600 !important; }

/* ════════════════════════════════════════════
   FORM LABELS — all input labels dark
   ════════════════════════════════════════════ */
.main .stTextInput label, .main .stNumberInput label,
.main .stSelectbox label, .main .stDateInput label,
.main .stTextArea label, .main .stToggle label,
.main .stRadio label, .main .stCheckbox label,
.main .stFileUploader label, .main .stMultiSelect label,
.main label { color: #334155 !important; font-weight: 500 !important; }

/* ════════════════════════════════════════════
   TEXT INPUTS — white bg, dark text
   ════════════════════════════════════════════ */
.main .stTextInput > div > div > input,
.main .stNumberInput > div > div > input,
.main .stTextArea > div > div > textarea,
.main input[type="text"], .main input[type="number"],
.main textarea {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
}

/* ════════════════════════════════════════════
   SELECTBOX — white bg, dark text
   ════════════════════════════════════════════ */
.main .stSelectbox > div > div,
.main .stSelectbox [data-baseweb="select"],
.main [data-baseweb="select"] > div,
.main [data-baseweb="select"] > div > div {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border-color: #CBD5E1 !important;
}
.main .stSelectbox [data-baseweb="select"] span,
.main [data-baseweb="select"] span { color: #1E293B !important; }

/* Dropdown menu */
[data-baseweb="popover"], [data-baseweb="menu"],
[role="listbox"], [data-baseweb="list"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
}
[data-baseweb="menu"] li, [role="option"],
[data-baseweb="list"] li { color: #1E293B !important; }
[data-baseweb="menu"] li:hover, [role="option"]:hover { background-color: #EFF6FF !important; }

/* ════════════════════════════════════════════
   DATE INPUT — white bg
   ════════════════════════════════════════════ */
.main .stDateInput > div > div > input,
.main .stDateInput > div > div {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border-color: #CBD5E1 !important;
}

/* ════════════════════════════════════════════
   NUMBER INPUT — white buttons
   ════════════════════════════════════════════ */
.main .stNumberInput > div > div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}
.main .stNumberInput button {
    background-color: #F1F5F9 !important;
    color: #334155 !important;
    border-color: #CBD5E1 !important;
}

/* ════════════════════════════════════════════
   FILE UPLOADER — white bg, dark text
   ════════════════════════════════════════════ */
.main .stFileUploader > div,
.main [data-testid="stFileUploader"],
.main [data-testid="stFileUploaderDropzone"],
.main [data-testid="stFileUploader"] > div,
.main [data-testid="stFileUploader"] section,
.main [data-testid="stFileUploader"] section > div,
.main .uploadedFile,
.main [data-testid="stFileUploaderDropzoneInstructions"],
.main [data-testid="stFileUploaderDropzoneInstructions"] div,
.main [data-testid="stFileUploaderDropzoneInstructions"] span,
.main [data-testid="stFileUploaderDropzoneInstructions"] small {
    background-color: #FFFFFF !important;
    color: #334155 !important;
    border-color: #CBD5E1 !important;
}
.main [data-testid="stFileUploaderDropzone"] {
    background-color: #FFFFFF !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 12px !important;
}
.main [data-testid="stFileUploaderDropzone"] * {
    color: #475569 !important;
}
.main [data-testid="stFileUploaderDropzone"] small {
    color: #64748B !important;
}
/* Browse button inside uploader */
.main [data-testid="stFileUploaderDropzone"] button,
.main [data-testid="baseButton-secondary"] {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ════════════════════════════════════════════
   TOGGLE — readable
   ════════════════════════════════════════════ */
.main .stToggle > label > span { color: #334155 !important; }
.main [data-testid="stToggle"] label span { color: #334155 !important; }

/* ════════════════════════════════════════════
   BUTTONS
   ════════════════════════════════════════════ */
.main .stButton > button[kind="primary"],
.main .stFormSubmitButton > button {
    background: linear-gradient(135deg, #1D4ED8, #2563EB) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.main .stButton > button[kind="primary"]:hover,
.main .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #1E40AF, #1D4ED8) !important;
}
.main .stButton > button:not([kind="primary"]) {
    border: 1px solid #CBD5E1 !important;
    color: #334155 !important;
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
}

/* ════════════════════════════════════════════
   TABS — blue active tab
   ════════════════════════════════════════════ */
.main .stTabs [data-baseweb="tab-list"] {
    background-color: #EFF6FF !important;
    border-radius: 10px; padding: 3px;
}
.main .stTabs [data-baseweb="tab"] { color: #475569 !important; font-weight: 500; }
.main .stTabs [aria-selected="true"] {
    background-color: #1D4ED8 !important;
    color: white !important; border-radius: 8px;
}

/* ════════════════════════════════════════════
   FORMS
   ════════════════════════════════════════════ */
.main [data-testid="stForm"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important; padding: 1.5rem;
}

/* ════════════════════════════════════════════
   EXPANDERS
   ════════════════════════════════════════════ */
.main .streamlit-expanderHeader,
.main details summary {
    background-color: #EFF6FF !important;
    color: #1E293B !important;
    font-weight: 600 !important;
    border-radius: 8px;
}
.main details summary span { color: #1E293B !important; }

/* ════════════════════════════════════════════
   DATAFRAMES
   ════════════════════════════════════════════ */
.main .stDataFrame { border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; }

/* ════════════════════════════════════════════
   ALERTS / INFO / WARNING
   ════════════════════════════════════════════ */
.main .stAlert { border-radius: 10px !important; }

/* ════════════════════════════════════════════
   DIVIDERS
   ════════════════════════════════════════════ */
.main hr { border-color: #E2E8F0 !important; }

/* ════════════════════════════════════════════
   DOWNLOAD BUTTON
   ════════════════════════════════════════════ */
.main .stDownloadButton > button {
    border: 1px solid #BFDBFE !important;
    color: #1D4ED8 !important;
    background-color: #EFF6FF !important;
    border-radius: 10px !important; font-weight: 600 !important;
}

/* ════════════════════════════════════════════
   TOAST / NOTIFICATIONS
   ════════════════════════════════════════════ */
[data-testid="stToast"] { background-color: #FFFFFF !important; color: #1E293B !important; }

/* ════════════════════════════════════════════
   SCROLLBAR
   ════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #94A3B8; border-radius: 3px; }

/* ════════════════════════════════════════════
   TEXT AREA (disabled — email viewer)
   ════════════════════════════════════════════ */
.main .stTextArea > div > div > textarea:disabled {
    background-color: #F8FAFC !important;
    color: #334155 !important;
}

/* ════════════════════════════════════════════
   TOP HEADER BAR
   ════════════════════════════════════════════ */
[data-testid="stHeader"] { background-color: #F8FAFC !important; }
header[data-testid="stHeader"] { background-color: #F8FAFC !important; }

/* ════════════════════════════════════════════
   TOOLBAR (Deploy button area)
   ════════════════════════════════════════════ */
[data-testid="stToolbar"] { background-color: transparent !important; }
[data-testid="stToolbar"] button { color: #475569 !important; }

/* ════════════════════════════════════════════
   PAGE HEADER BANNER
   ════════════════════════════════════════════ */
.page-header {
    background: linear-gradient(135deg, #0F2A4A 0%, #1D4ED8 100%);
    border-radius: 14px; padding: 1.3rem 2rem; margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 1rem;
    box-shadow: 0 4px 15px rgba(15,42,74,0.15);
}
.page-header-icon { font-size: 2rem; }
.page-header-title { font-size: 1.5rem; font-weight: 700; color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important; margin: 0; line-height: 1.2; }
.page-header-sub { font-size: 0.85rem; color: #BFDBFE !important;
    -webkit-text-fill-color: #BFDBFE !important; margin: 0; }
.page-header-brand { margin-left: auto; font-size: 0.75rem; color: #93C5FD !important;
    -webkit-text-fill-color: #93C5FD !important; font-weight: 500; }
</style>
"""


def page_header(icon: str, title: str, subtitle: str = ""):
    """Render a branded page header banner."""
    import streamlit as st
    sub_html = f'<div class="page-header-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-icon">{icon}</div>
        <div>
            <div class="page-header-title">{title}</div>
            {sub_html}
        </div>
        <div class="page-header-brand">🏦 FCFE Agent</div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_branding():
    """Render sidebar branding block."""
    import streamlit as st
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 1rem;">
            <div style="font-size:1.8rem;">🏦</div>
            <div style="font-size:0.85rem; font-weight:700; color:#E2E8F0 !important; line-height:1.3;">Finance Credit<br>Follow-Up Email Agent</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

