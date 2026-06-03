"""
================================================================================
تولید داده بانکی با نسبت متوازن واقعی (30% تایید - 70% رد)
نسخه بهینه شده برای دقت 90%
================================================================================
"""

import sqlite3
import random
import numpy as np
from faker import Faker

fake = Faker("fa_IR")

np.random.seed(42)
random.seed(42)

# -----------------------------
# CONFIG
# -----------------------------
N_HISTORICAL = 5000  # افزایش داده برای دقت بهتر (از 4000 به 5000)
N_UNSEEN = 1000  # داده جدید (بدون برچسب - approved = NULL)

conn = sqlite3.connect("loan_manager_app/bank.db")
cursor = conn.cursor()

# -----------------------------
# DROP & CREATE TABLES
# -----------------------------
cursor.executescript("""
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employments;
DROP TABLE IF EXISTS credit_profiles;
DROP TABLE IF EXISTS loan_requests;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    national_id TEXT,
    phone_number TEXT,
    age INTEGER,
    marital_status TEXT,
    dependents INTEGER
);

CREATE TABLE employments (
    customer_id INTEGER,
    employment_type TEXT,
    employment_years REAL,
    monthly_income INTEGER
);

CREATE TABLE credit_profiles (
    customer_id INTEGER,
    credit_score INTEGER
);

CREATE TABLE loan_requests (
    customer_id INTEGER,
    loan_amount INTEGER,
    loan_term_months INTEGER,
    loan_purpose TEXT,
    has_other_loans INTEGER,
    late_payments_last_year INTEGER,
    approved INTEGER  -- NULL = داده جدید (unseen)
);
""")

# -----------------------------
# CONSTANTS
# -----------------------------
employment_types = ["کارمند", "آزاد", "دولتی", "فریلنس", "بیکار", "بازنشسته"]
loan_purposes = ["مسکن", "خودرو", "کسب_و_کار", "شخصی", "تحصیل", "پزشکی"]
marital_statuses = ["مجرد", "متأهل"]


def generate_customer_data(cursor, is_unseen=False):
    """تولید یک رکورد کامل مشتری و برگرداندن customer_id"""

    # ----- CUSTOMER -----
    age = random.randint(22, 65)
    marital = random.choice(marital_statuses)
    dependents = 0 if marital == "مجرد" else random.randint(1, 4)

    cursor.execute(
        """
        INSERT INTO customers VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            fake.first_name(),
            fake.last_name(),
            str(random.randint(1000000000, 9999999999)),
            "09" + str(random.randint(100000000, 999999999)),
            age,
            marital,
            dependents,
        ),
    )

    cid = cursor.lastrowid

    # ----- EMPLOYMENT -----
    if age > 55:
        emp_type = random.choices(["بازنشسته", "دولتی", "آزاد"], weights=[0.4, 0.3, 0.3])[0]
    elif age < 25:
        emp_type = random.choices(["کارمند", "آزاد", "فریلنس", "بیکار"], weights=[0.3, 0.3, 0.3, 0.1])[0]
    else:
        emp_type = random.choices(employment_types[:-1], weights=[0.4, 0.2, 0.2, 0.15, 0.05])[0]

    if emp_type == "بیکار":
        emp_years = 0
    elif emp_type == "بازنشسته":
        emp_years = min(35, max(10, age - 25 + random.randint(-5, 5)))
    else:
        emp_years = min(age - 20, max(0, int(np.random.normal(age - 30, 5))))

    base_income = {
        "کارمند": 12_000_000,
        "دولتی": 18_000_000,
        "آزاد": 20_000_000,
        "فریلنس": 22_000_000,
        "بیکار": 3_000_000,
        "بازنشسته": 8_000_000,
    }[emp_type]

    income = base_income + emp_years * 500_000
    # ✅ تغییر 1: کاهش نویز از 15% به 8% (برای دقت بالاتر)
    income = int(income * random.uniform(0.92, 1.08))
    income = max(2_000_000, income)

    cursor.execute(
        """
        INSERT INTO employments VALUES (?, ?, ?, ?)
    """,
        (cid, emp_type, emp_years, income),
    )

    # ----- CREDIT SCORE -----
    credit_score = int(400 + (income / 1_000_000) * 10 + emp_years * 8)
    # ✅ تغییر 2: کاهش نویز از 15% به 8%
    credit_score = int(credit_score * random.uniform(0.92, 1.08))
    credit_score = max(350, min(850, credit_score))

    # 2% missing value (کاهش از 3% به 2%)
    if random.random() < 0.02 and not is_unseen:
        credit_score = None

    cursor.execute(
        """
        INSERT INTO credit_profiles VALUES (?, ?)
    """,
        (cid, credit_score),
    )

    # ----- LOAN REQUEST -----
    loan_amount = income * random.uniform(2, 8)
    loan_amount = max(5_000_000, min(500_000_000, int(loan_amount)))
    loan_term = random.choice([12, 24, 36, 48, 60, 72])
    purpose = random.choice(loan_purposes)
    has_other_loans = 1 if (income > 20_000_000 and age < 45 and random.random() < 0.3) else 0

    if credit_score and credit_score > 700:
        late_payments = np.random.poisson(0.1)  # کاهش تاخیرها
    elif credit_score and credit_score > 550:
        late_payments = np.random.poisson(0.5)  # کاهش تاخیرها
    else:
        late_payments = np.random.poisson(1.5)  # کاهش تاخیرها
    late_payments = min(4, late_payments)  # کاهش حداکثر از 5 به 4

    return cid, {
        "age": age,
        "dependents": dependents,
        "employment_years": emp_years,
        "monthly_income": income,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "loan_term_months": loan_term,
        "loan_purpose": purpose,
        "has_other_loans": has_other_loans,
        "late_payments_last_year": late_payments,
        "marital_status": marital,
        "employment_type": emp_type,
    }


def calculate_approval(data):
    """محاسبه تایید یا رد وام - بهینه شده برای دقت 90%"""

    monthly_installment = data["loan_amount"] / data["loan_term_months"]
    dti = monthly_installment / data["monthly_income"]
    credit_score = data["credit_score"]

    # اگر credit_score گمشده باشد
    if credit_score is None:
        return 1 if random.random() < 0.25 else 0  # افزایش از 20% به 25%

    # ✅ تغییر 3: قوانین واضح‌تر و کاهش نویز

    # قانون 1: تایید قطعی (شرایط عالی)
    if credit_score >= 720 and dti <= 0.30 and data["late_payments_last_year"] == 0:
        return 1

    # قانون 2: تایید با اطمینان بالا
    elif credit_score >= 680 and dti <= 0.35 and data["employment_years"] >= 4 and data["late_payments_last_year"] <= 1:
        # ✅ افزایش شانس از 70% به 85%
        return 1 if random.random() < 0.85 else 0

    # قانون 3: وام مسکن
    elif (
        credit_score >= 650 and dti <= 0.40 and data["loan_purpose"] == "مسکن" and data["late_payments_last_year"] <= 1
    ):
        # ✅ افزایش شانس از 60% به 80%
        return 1 if random.random() < 0.80 else 0

    # قانون 4: رد قطعی
    elif dti > 0.52 or data["late_payments_last_year"] >= 3 or credit_score < 550:
        return 0

    # قانون 5: موارد مرزی (با دقت بالاتر)
    else:
        # ✅ بهبود فرمول محاسبه احتمال
        prob = (credit_score - 550) / 250 * 0.5 + (1 - dti) * 0.4 - (data["late_payments_last_year"] * 0.08)
        prob = max(0.1, min(0.45, prob))
        # ✅ کاهش نویز از 20% به 10%
        prob = prob * random.uniform(0.90, 1.10)
        prob = max(0, min(0.55, prob))
        return 1 if random.random() < prob else 0


# ============================================================================
# تولید داده‌های تاریخی (با برچسب)
# ============================================================================
print("\n" + "=" * 70)
print("مرحله 1: تولید داده‌های تاریخی (30% تایید - 70% رد)")
print("=" * 70)

approved_count = 0
rejected_count = 0

for i in range(N_HISTORICAL):
    cid, data = generate_customer_data(cursor, is_unseen=False)
    approved = calculate_approval(data)

    if approved == 1:
        approved_count += 1
    else:
        rejected_count += 1

    cursor.execute(
        """
        INSERT INTO loan_requests VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cid,
            data["loan_amount"],
            data["loan_term_months"],
            data["loan_purpose"],
            data["has_other_loans"],
            data["late_payments_last_year"],
            approved,
        ),
    )

    if (i + 1) % 1000 == 0:
        print(f"   {i + 1} رکورد تاریخی تولید شد (تایید: {approved_count}, رد: {rejected_count})")

print(f"\n📊 نسبت نهایی داده تاریخی:")
print(f"   تایید شده: {approved_count} ({approved_count / N_HISTORICAL * 100:.1f}%)")
print(f"   رد شده: {rejected_count} ({rejected_count / N_HISTORICAL * 100:.1f}%)")

# ============================================================================
# تولید داده‌های جدید (unseen - بدون برچسب)
# ============================================================================
print("\n" + "=" * 70)
print("مرحله 2: تولید داده‌های جدید (unseen - approved = NULL)")
print("=" * 70)

for i in range(N_UNSEEN):
    cid, data = generate_customer_data(cursor, is_unseen=True)

    cursor.execute(
        """
        INSERT INTO loan_requests VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cid,
            data["loan_amount"],
            data["loan_term_months"],
            data["loan_purpose"],
            data["has_other_loans"],
            data["late_payments_last_year"],
            None,
        ),
    )

    if (i + 1) % 500 == 0:
        print(f"   {i + 1} رکورد unseen تولید شد")

conn.commit()

# ============================================================================
# گزارش نهایی
# ============================================================================
print("\n" + "=" * 70)
print("✅ دیتابیس با کیفیت بالا (مناسب دقت 90%) تولید شد")
print("=" * 70)

cursor.execute("SELECT COUNT(*) FROM loan_requests WHERE approved IS NOT NULL")
historical_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM loan_requests WHERE approved IS NULL")
unseen_count = cursor.fetchone()[0]

print(f"\n📊 آمار نهایی:")
print(f"   داده‌های تاریخی: {historical_count:,} رکورد")
print(f"   داده‌های جدید (unseen): {unseen_count:,} رکورد")

cursor.execute("""
    SELECT approved, COUNT(*) FROM loan_requests 
    WHERE approved IS NOT NULL GROUP BY approved
""")
print(f"\n🎯 توزیع هدف در داده‌های تاریخی:")
for val, count in cursor.fetchall():
    label = "تایید شده" if val == 1 else "رد شده"
    pct = count / historical_count * 100
    print(f"   {label}: {count} ({pct:.1f}%)")

print(f"\n💾 دیتابیس ذخیره شد: loan_manager_app/bank.db")
print("\n✅ تغییرات اعمال شده برای دقت 90%:")
print("   1. افزایش داده تاریخی از 4000 به 5000 رکورد")
print("   2. کاهش نویز درآمد و credit_score از 15% به 8%")
print("   3. کاهش missing values از 3% به 2%")
print("   4. کاهش نویز در قوانین تصمیم‌گیری")
print("   5. افزایش شانس تایید در قوانین 2 و 3")

conn.close()
