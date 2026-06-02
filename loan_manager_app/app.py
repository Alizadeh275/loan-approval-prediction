# app.py
import streamlit as st

# ماژول‌های داخلی
from config import setup_page
from styles import load_css
from database import (
    init_manager_tables,
    get_total_count,
    load_loan_requests_paginated,
    load_all_for_stats,
    export_to_excel,
)
from model_utils import load_model
from components import render_header, render_sidebar, render_stats, render_loan_card, render_pagination

# ============================================================================
# Setup
# ============================================================================
setup_page()
load_css()
render_header()

# ============================================================================
# Initialize Database
# ============================================================================
init_manager_tables()

# ============================================================================
# Load Model
# ============================================================================
try:
    model_package = load_model()
    model = model_package["model"]
    employment_encoder = model_package["employment_encoder"]
    purpose_encoder = model_package["purpose_encoder"]
except Exception as e:
    st.error(f"❌ خطا در بارگذاری مدل: {e}")
    st.stop()

# ============================================================================
# Sidebar
# ============================================================================
status_filter, items_per_page, export_clicked = render_sidebar()

# خروجی Excel
if export_clicked:
    df_export = export_to_excel(status_filter)
    df_export.to_excel("loan_requests_export.xlsx", index=False)
    st.success("✅ فایل Excel ذخیره شد")

# ============================================================================
# Statistics
# ============================================================================
df_stats = load_all_for_stats(status_filter)
total_all = get_total_count("all")
render_stats(df_stats, total_all)

# ============================================================================
# Pagination State
# ============================================================================
if "page_number" not in st.session_state:
    st.session_state.page_number = 1

total_count = get_total_count(status_filter)
total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)

if st.session_state.page_number > total_pages:
    st.session_state.page_number = total_pages
if st.session_state.page_number < 1:
    st.session_state.page_number = 1

offset = (st.session_state.page_number - 1) * items_per_page

# ============================================================================
# Load and Display Data
# ============================================================================
df = load_loan_requests_paginated(status_filter, items_per_page, offset)

st.markdown(f"### 📋 لیست درخواست‌ها (صفحه {st.session_state.page_number} از {total_pages})")
st.markdown("---")

if len(df) == 0:
    st.info("ℹ️ هیچ درخواستی با این فیلتر وجود ندارد")
    st.stop()

# نمایش هر درخواست
for idx, row in df.iterrows():
    render_loan_card(row, model, employment_encoder, purpose_encoder)

# ============================================================================
# Pagination Controls
# ============================================================================
render_pagination(st.session_state.page_number, total_pages)
