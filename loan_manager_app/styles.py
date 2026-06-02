# styles.py
import streamlit as st


def load_css():
    """بارگذاری استایل‌های CSS"""
    st.markdown(
        """
    <style>
        /* راست‌چین کردن کل محتوای اصلی */
        .main > div {
            direction: rtl;
        }
        
        .block-container {
            direction: rtl;
        }
        
        .main p, .main div, .main span, .main label, .main h1, .main h2, .main h3, .main h4,
        .stMarkdown, .stMarkdown p, .stMarkdown div {
            direction: rtl;
            text-align: right;
        }
        
        div[data-testid="column"] {
            direction: rtl;
            text-align: right;
        }
        
        [data-testid="stMetricValue"] {
            direction: rtl;
            text-align: center;
        }
        
        [data-testid="stMetricLabel"] {
            direction: rtl;
            text-align: center;
        }
        
        [data-testid="stSidebar"] .block-container {
            direction: rtl;
        }
        
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown {
            direction: rtl;
            text-align: right;
        }
        
        .stSelectbox label {
            direction: rtl;
            text-align: right;
            width: 100%;
        }
        
        .stButton button {
            direction: rtl;
        }
        
        .stForm {
            direction: rtl;
        }
        
        .stProgress > div > div {
            direction: ltr !important;
        }
        
        .main-header {
            text-align: center;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        
        .info-card {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 10px;
            border-right: 4px solid #339af0;
            margin: 5px 0;
        }
        
        .success-text {
            color: #51cf66;
            font-weight: bold;
        }
        
        .error-text {
            color: #ff6b6b;
            font-weight: bold;
        }
        
        .pagination-container {
            direction: ltr;
            text-align: center;
            margin: 20px 0;
        }
        .stButton button {
            margin: 0 5px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
