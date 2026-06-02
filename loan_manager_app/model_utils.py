# model_utils.py
import streamlit as st
import pandas as pd
import joblib
from config import MODEL_PATH


@st.cache_resource
def load_model():
    """بارگذاری مدل و انکودرها"""
    model_package = joblib.load(MODEL_PATH)
    return model_package


def prepare_features(row, employment_encoder, purpose_encoder):
    """آماده‌سازی ویژگی‌ها برای پیش‌بینی"""
    marital_num = 1 if row["marital_status"] == "متأهل" else 0
    employment_num = employment_encoder.transform([row["employment_type"]])[0]
    purpose_num = purpose_encoder.transform([row["loan_purpose"]])[0]

    features_dict = {
        "age": [row["age"]],
        "dependents": [row["dependents"]],
        "employment_years": [row["employment_years"]],
        "monthly_income": [row["monthly_income"]],
        "credit_score": [row["credit_score"] if pd.notna(row["credit_score"]) else 600],
        "loan_amount": [row["loan_amount"]],
        "loan_term_months": [row["loan_term_months"]],
        "has_other_loans": [row["has_other_loans"]],
        "late_payments_last_year": [row["late_payments_last_year"]],
        "marital_num": [marital_num],
        "employment_num": [employment_num],
        "purpose_num": [purpose_num],
    }

    return pd.DataFrame(features_dict)


def get_prediction(model, features):
    """دریافت پیش‌بینی و احتمال از مدل"""
    prob = model.predict_proba(features)[0][1]
    prediction = "تایید" if prob >= 0.5 else "رد"
    return prediction, prob
