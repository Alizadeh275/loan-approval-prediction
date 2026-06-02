# components.py
import streamlit as st
import pandas as pd
from database import update_loan_status


def render_header():
    """نمایش هدر اصلی"""
    st.markdown('<div class="main-header">🏦 سیستم مدیریت درخواست‌های وام</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """نمایش سایدبار"""
    with st.sidebar:
        st.markdown("## 🔍 فیلترها")
        st.markdown("---")

        status_filter = st.selectbox(
            "وضعیت درخواست‌ها",
            ["all", "pending_manager", "approved_by_manager", "rejected_by_manager"],
            format_func=lambda x: {
                "all": "📋 همه درخواست‌ها",
                "pending_manager": "⏳ نیاز به بررسی مدیر",
                "approved_by_manager": "✅ تایید شده توسط مدیر",
                "rejected_by_manager": "❌ رد شده توسط مدیر",
            }[x],
        )

        items_per_page = st.selectbox("تعداد در هر صفحه", [5, 10, 20, 50], index=1)

        st.markdown("---")
        st.markdown("### 📥 خروجی")

        export_clicked = st.button("📊 خروجی Excel", use_container_width=True)

        st.markdown("---")
        st.caption("💡 همه درخواست‌ها باید توسط مدیر تایید یا رد شوند")

        return status_filter, items_per_page, export_clicked


def render_stats(df_stats, total_all):
    """نمایش آمار"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📋 کل درخواست‌ها", f"{total_all:,}")
    with col2:
        manager_approved = len(df_stats[df_stats["approved_by_manager"] == 1]) if len(df_stats) > 0 else 0
        st.metric("👨‍💼 تأیید توسط مدیر", f"{manager_approved:,}")
    with col3:
        manager_rejected = len(df_stats[df_stats["approved_by_manager"] == 0]) if len(df_stats) > 0 else 0
        st.metric("👨‍💼 رد توسط مدیر", f"{manager_rejected:,}")
    with col4:
        pending = len(df_stats[df_stats["approved_by_manager"].isna()]) if len(df_stats) > 0 else 0
        st.metric("⏳ در انتظار تایید مدیر", f"{pending:,}")

    st.markdown("---")


def render_loan_card(row, model, employment_encoder, purpose_encoder):
    """نمایش یک کارت درخواست وام"""
    from model_utils import prepare_features, get_prediction

    with st.container():
        st.markdown(f'<div class="info-card">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        # پیش‌بینی مدل
        features = prepare_features(row, employment_encoder, purpose_encoder)
        ai_prediction, pred_prob = get_prediction(model, features)

        with col1:
            st.markdown(f"""
            **👤 نام:** {row["first_name"]} {row["last_name"]}  
            **🆔 کد ملی:** {row["national_id"]}  
            **🎂 سن:** {row["age"]} سال  
            **👨‍👩‍👧 افراد تحت تکفل:** {row["dependents"]}  
            **💍 وضعیت تاهل:** {row["marital_status"]}
            """)

        with col2:
            income_million = row["monthly_income"] / 1_000_000
            loan_million = row["loan_amount"] / 1_000_000

            st.markdown(f"""
            **💼 نوع اشتغال:** {row["employment_type"]}  
            **📅 سابقه کار:** {row["employment_years"]} سال  
            **💰 درآمد ماهانه:** {income_million:,.1f} میلیون تومان  
            **💸 مبلغ وام:** {loan_million:,.1f} میلیون تومان  
            **📊 نمره اعتباری:** {row["credit_score"] if pd.notna(row["credit_score"]) else "نامشخص"}
            """)

        with col3:
            if ai_prediction == "تایید":
                st.markdown(
                    f'<span class="success-text">🤖 پیشنهاد AI: {ai_prediction} (احتمال {pred_prob * 100:.1f}%)</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<span class="error-text">🤖 پیشنهاد AI: {ai_prediction} (احتمال {pred_prob * 100:.1f}%)</span>',
                    unsafe_allow_html=True,
                )

            st.progress(pred_prob)
            st.caption(f"📈 احتمال تایید از نظر AI: {pred_prob * 100:.1f}%")

            if not pd.isna(row["approved_by_manager"]):
                if row["approved_by_manager"] == 1:
                    st.markdown('<span class="success-text">✅ تصمیم نهایی مدیر: تایید</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="error-text">❌ تصمیم نهایی مدیر: رد</span>', unsafe_allow_html=True)

                if pd.notna(row["manager_comment"]) and row["manager_comment"]:
                    st.caption(f"💬 نظر مدیر: {row['manager_comment']}")
                if pd.notna(row["manager_review_date"]):
                    st.caption(f"📅 تاریخ بررسی: {row['manager_review_date'][:10]}")
            else:
                st.warning("⏳ در انتظار تصمیم مدیر")

        with col4:
            if pd.isna(row["approved_by_manager"]):
                with st.form(key=f"form_{row['loan_id']}"):
                    comment = st.text_input(
                        "✏️ نظر مدیر", key=f"comment_{row['loan_id']}", placeholder="دلیل تصمیم خود را وارد کنید..."
                    )

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        approve_btn = st.form_submit_button("✅ تایید", type="primary", use_container_width=True)
                    with btn_col2:
                        reject_btn = st.form_submit_button("❌ رد", type="secondary", use_container_width=True)

                    if approve_btn:
                        update_loan_status(row["loan_id"], 1, comment)
                        st.success("✅ درخواست تایید شد!")
                        st.rerun()

                    if reject_btn:
                        update_loan_status(row["loan_id"], 0, comment)
                        st.error("❌ درخواست رد شد!")
                        st.rerun()
            else:
                if row["approved_by_manager"] == 1:
                    st.success("✅ تایید شده")
                else:
                    st.error("❌ رد شده")

                if st.button("🔄 تغییر تصمیم", key=f"change_{row['loan_id']}", use_container_width=True):
                    update_loan_status(row["loan_id"], None, "")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


def render_pagination(current_page, total_pages):
    """نمایش کنترل‌های صفحه‌بندی"""
    st.markdown("---")
    col_prev, col_page_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if current_page > 1:
            if st.button("⬅️ صفحه قبلی", use_container_width=True):
                st.session_state.page_number = current_page - 1
                st.rerun()

    with col_page_info:
        st.markdown(
            f'<div style="text-align: center; direction: ltr;">صفحه {current_page} از {total_pages}</div>',
            unsafe_allow_html=True,
        )

    with col_next:
        if current_page < total_pages:
            if st.button("صفحه بعدی ➡️", use_container_width=True):
                st.session_state.page_number = current_page + 1
                st.rerun()
