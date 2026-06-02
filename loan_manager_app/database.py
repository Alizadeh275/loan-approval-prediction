# database.py
import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH


def init_manager_tables():
    """افزودن ستون‌های مدیریت به دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(loan_requests)")
    columns = [col[1] for col in cursor.fetchall()]

    if "approved_by_manager" not in columns:
        cursor.execute("ALTER TABLE loan_requests ADD COLUMN approved_by_manager INTEGER")
    if "manager_comment" not in columns:
        cursor.execute("ALTER TABLE loan_requests ADD COLUMN manager_comment TEXT")
    if "manager_review_date" not in columns:
        cursor.execute("ALTER TABLE loan_requests ADD COLUMN manager_review_date TEXT")

    conn.commit()
    conn.close()


def get_where_clause(status_filter):
    """دریافت شرط WHERE بر اساس فیلتر"""
    if status_filter == "pending_manager":
        return "l.approved IS NULL and l.approved_by_manager IS NULL"
    elif status_filter == "approved_by_manager":
        return "l.approved IS NULL and l.approved_by_manager = 1"
    elif status_filter == "rejected_by_manager":
        return "l.approved IS NULL and l.approved_by_manager = 0"
    else:
        return "l.approved IS NULL"


def get_total_count(status_filter="all"):
    """دریافت تعداد کل رکوردها"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    where_clause = get_where_clause(status_filter)

    query = f"""
    SELECT COUNT(*)
    FROM customers c
    JOIN employments e ON c.customer_id = e.customer_id
    JOIN credit_profiles cp ON c.customer_id = cp.customer_id
    JOIN loan_requests l ON c.customer_id = l.customer_id
    WHERE {where_clause}
    """

    cursor.execute(query)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def load_loan_requests_paginated(status_filter="all", limit=10, offset=0):
    """بارگذاری صفحه‌بندی شده درخواست‌ها"""
    conn = sqlite3.connect(DB_PATH)
    where_clause = get_where_clause(status_filter)

    query = f"""
    SELECT 
        c.customer_id,
        c.age,
        c.marital_status,
        c.dependents,
        e.employment_type,
        e.employment_years,
        e.monthly_income,
        cp.credit_score,
        l.rowid as loan_id,
        l.loan_amount,
        l.loan_term_months,
        l.loan_purpose,
        l.has_other_loans,
        l.late_payments_last_year,
        l.approved as current_status,
        l.approved_by_manager,
        l.manager_comment,
        l.manager_review_date,
        c.first_name,
        c.last_name,
        c.national_id
    FROM customers c
    JOIN employments e ON c.customer_id = e.customer_id
    JOIN credit_profiles cp ON c.customer_id = cp.customer_id
    JOIN loan_requests l ON c.customer_id = l.customer_id
    WHERE {where_clause}
    ORDER BY l.rowid DESC
    LIMIT {limit} OFFSET {offset}
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def load_all_for_stats(status_filter="all"):
    """بارگذاری فقط برای آمار"""
    conn = sqlite3.connect(DB_PATH)
    where_clause = get_where_clause(status_filter).replace("l.", "")

    query = f"""
    SELECT 
        approved as current_status,
        approved_by_manager
    FROM loan_requests l
    WHERE {where_clause}
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def update_loan_status(loan_id, approved_by_manager, comment):
    """به‌روزرسانی وضعیت وام"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE loan_requests
        SET approved_by_manager = ?,
            manager_comment = ?,
            manager_review_date = ?
        WHERE rowid = ?
    """,
        (approved_by_manager, comment, datetime.now().isoformat(), loan_id),
    )
    conn.commit()
    conn.close()


def export_to_excel(status_filter):
    """خروجی اکسل"""
    conn = sqlite3.connect(DB_PATH)
    where_clause = get_where_clause(status_filter)

    query = f"""
    SELECT 
        c.first_name, c.last_name, c.national_id, c.age, c.marital_status,
        e.employment_type, e.monthly_income,
        l.loan_amount, l.loan_term_months, l.loan_purpose,
        l.approved as ai_status, l.approved_by_manager as manager_status, l.manager_comment
    FROM customers c
    JOIN employments e ON c.customer_id = e.customer_id
    JOIN loan_requests l ON c.customer_id = l.customer_id
    WHERE {where_clause}
    """
    df_export = pd.read_sql(query, conn)
    conn.close()
    return df_export
