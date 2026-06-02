# config.py
import streamlit as st


# تنظیمات صفحه
def setup_page():
    st.set_page_config(page_title="بانک - سیستم مدیریت وام", page_icon="🏦", layout="wide")


# نام دیتابیس
DB_PATH = "loan_manager_app/bank.db"
MODEL_PATH = "loan_manager_app/artifacts/loan_model.pkl"

# تعداد آیتم در هر صفحه (پیش‌فرض)
DEFAULT_ITEMS_PER_PAGE = 10
ITEMS_PER_PAGE_OPTIONS = [5, 10, 20, 50]

# گزینه‌های فیلتر وضعیت
STATUS_FILTERS = {
    "all": "📋 همه درخواست‌ها",
    "pending_manager": "⏳ نیاز به بررسی مدیر",
    "approved_by_manager": "✅ تایید شده توسط مدیر",
    "rejected_by_manager": "❌ رد شده توسط مدیر",
}


# تابع کمکی برای نمایش فارسی فیلترها
def format_status_filter(key):
    return STATUS_FILTERS.get(key, key)
