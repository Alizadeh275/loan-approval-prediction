"""
================================================================================
Complete Machine Learning Course - Loan Approval Prediction
Simple Version with Decision Tree (Easy to Understand) - No Scaling
================================================================================
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder  # StandardScaler حذف شد
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.tree import export_text

ARTIFACT_FOLDER = "loan_manager_app/artifacts"

print("✅ Libraries loaded successfully")

# ============================================================================
# Step 1: Load Data from Database
# ============================================================================
print("\n" + "=" * 70)
print("Step 1: Load Data from Database")
print("=" * 70)

conn = sqlite3.connect("loan_manager_app/bank.db")

query = """
SELECT 
    c.age,
    c.marital_status,
    c.dependents,
    e.employment_type,
    e.employment_years,
    e.monthly_income,
    cp.credit_score,
    l.loan_amount,
    l.loan_term_months,
    l.loan_purpose,
    l.has_other_loans,
    l.late_payments_last_year,
    l.approved
FROM customers c
JOIN employments e ON c.customer_id = e.customer_id
JOIN credit_profiles cp ON c.customer_id = cp.customer_id
JOIN loan_requests l ON c.customer_id = l.customer_id
WHERE l.approved IS NOT NULL
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"Total records: {len(df):,}")
print(f"Total features: {len(df.columns)}")

print("\n📊 Target Distribution (approved):")
print(df["approved"].value_counts())
print(f"Approval rate: {df['approved'].mean() * 100:.1f}%")

# ============================================================================
# Step 2: Exploratory Data Analysis (EDA)
# ============================================================================
print("\n" + "=" * 70)
print("Step 2: Exploratory Data Analysis (EDA)")
print("=" * 70)

# 2.1 Descriptive Statistics
print("\n📈 Descriptive Statistics of Numerical Features:")
print(df.describe())

# 2.2 Missing Values
print("\n🔍 Missing Values:")
print(df.isnull().sum())

# 2.3 Target Distribution
print("\n🎯 Target Distribution (approved):")
target_dist = df["approved"].value_counts(normalize=True)
print(f"   Rejected (0): {target_dist.get(0, 0) * 100:.1f}%")
print(f"   Approved (1): {target_dist.get(1, 0) * 100:.1f}%")

# ============================================================================
# Step 3: Data Visualizations
# ============================================================================
print("\n" + "=" * 70)
print("Step 3: Data Visualizations")
print("=" * 70)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle("Exploratory Data Analysis - Loan Approval Dataset", fontsize=14, fontweight="bold")

# Plot 1: Target Distribution (Bar Chart)
ax1 = axes[0, 0]
target_counts = df["approved"].value_counts()
colors = ["#ff6b6b", "#51cf66"]
ax1.bar(["Rejected", "Approved"], target_counts.values, color=colors)
ax1.set_title("Target Distribution", fontsize=12)
ax1.set_ylabel("Count")

# Plot 2: Age Distribution
ax2 = axes[0, 1]
ax2.hist(df["age"], bins=20, color="#339af0", edgecolor="black", alpha=0.7)
ax2.set_title("Age Distribution", fontsize=12)
ax2.set_xlabel("Age")
ax2.set_ylabel("Frequency")

# Plot 3: Credit Score by Approval Status
ax3 = axes[0, 2]
df.boxplot(column="credit_score", by="approved", ax=ax3, patch_artist=True)
ax3.set_title("Credit Score by Approval Status", fontsize=12)
ax3.set_xlabel("Approval Status")
ax3.set_ylabel("Credit Score")
ax3.set_xticklabels(["Rejected", "Approved"])

# Plot 4: Monthly Income Distribution
ax4 = axes[1, 0]
ax4.hist(df["monthly_income"] / 1_000_000, bins=25, color="#fcc419", edgecolor="black", alpha=0.7)
ax4.set_title("Monthly Income Distribution", fontsize=12)
ax4.set_xlabel("Income (Million Toman)")
ax4.set_ylabel("Frequency")

# Plot 5: Employment Years by Approval
ax5 = axes[1, 1]
df.boxplot(column="employment_years", by="approved", ax=ax5, patch_artist=True)
ax5.set_title("Employment Years by Approval Status", fontsize=12)
ax5.set_xlabel("Approval Status")
ax5.set_ylabel("Employment Years")
ax5.set_xticklabels(["Rejected", "Approved"])

# Plot 6: Loan Amount vs Income (Scatter)
ax6 = axes[1, 2]
approved = df[df["approved"] == 1]
rejected = df[df["approved"] == 0]
ax6.scatter(approved["monthly_income"] / 1e6, approved["loan_amount"] / 1e6, alpha=0.5, c="green", label="Approved")
ax6.scatter(rejected["monthly_income"] / 1e6, rejected["loan_amount"] / 1e6, alpha=0.5, c="red", label="Rejected")
ax6.set_title("Loan Amount vs Income", fontsize=12)
ax6.set_xlabel("Monthly Income (Million Toman)")
ax6.set_ylabel("Loan Amount (Million Toman)")
ax6.legend()

plt.tight_layout()
plt.savefig(f"{ARTIFACT_FOLDER}/eda_plots.png", dpi=150)
print("✅ EDA plots saved: eda_plots.png")

# ============================================================================
# Step 4: Data Cleaning
# ============================================================================
print("\n" + "=" * 70)
print("Step 4: Data Cleaning")
print("=" * 70)

# Remove duplicates
before_dup = len(df)
df = df.drop_duplicates()
print(f"Duplicates removed: {before_dup - len(df)}")

# Handle missing values
print(f"\nMissing values before cleaning:")
print(df.isnull().sum())

if df["credit_score"].isnull().sum() > 0:
    median_score = df["credit_score"].median()
    df["credit_score"] = df["credit_score"].fillna(median_score)
    print(f"✅ credit_score filled with median: {median_score:.0f}")

print("\n✅ Data cleaning completed")

# ============================================================================
# Step 5: Encoding (Required for Decision Tree)
# ============================================================================
print("\n" + "=" * 70)
print("Step 5: Encoding Categorical Variables")
print("=" * 70)

df["marital_num"] = df["marital_status"].map({"مجرد": 0, "متأهل": 1})

le_employment = LabelEncoder()
df["employment_num"] = le_employment.fit_transform(df["employment_type"])

le_purpose = LabelEncoder()
df["purpose_num"] = le_purpose.fit_transform(df["loan_purpose"])

df = df.drop(columns=["marital_status", "employment_type", "loan_purpose"])

print("✅ Encoding completed")
print(f"   marital_status: Single=0, Married=1")
print(f"   employment_type: {dict(zip(le_employment.classes_, range(len(le_employment.classes_))))}")
print(f"   loan_purpose: {dict(zip(le_purpose.classes_, range(len(le_purpose.classes_))))}")

# ============================================================================
# Step 6: Feature Selection
# ============================================================================
print("\n" + "=" * 70)
print("Step 6: Feature Selection")
print("=" * 70)

feature_columns = [
    "age",
    "dependents",
    "employment_years",
    "monthly_income",
    "credit_score",
    "loan_amount",
    "loan_term_months",
    "has_other_loans",
    "late_payments_last_year",
    "marital_num",
    "employment_num",
    "purpose_num",
]

X = df[feature_columns]
y = df["approved"]

print(f"X shape: {X.shape}")
print(f"y shape: {y.shape}")

# ============================================================================
# Step 7: Train-Test Split
# ============================================================================
print("\n" + "=" * 70)
print("Step 7: Train-Test Split")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"Training data: {X_train.shape}")
print(f"Test data: {X_test.shape}")
print("✅ No scaling needed - Decision Tree works with original values")

# ============================================================================
# Step 8: Train Decision Tree Model
# ============================================================================
print("\n" + "=" * 70)
print("Step 8: Train Decision Tree Model")
print("=" * 70)

model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_split=10,
    class_weight="balanced",  # ← این خط را اضافه کنید
    random_state=42,
)

model.fit(X_train, y_train)
print("✅ Decision Tree model trained")

# ============================================================================
# Step 9: Visualize the Decision Tree
# ============================================================================
print("\n" + "=" * 70)
print("Step 9: Visualize the Decision Tree")
print("=" * 70)

# تصویر بزرگ
plt.figure(figsize=(60, 30))
plot_tree(
    model, feature_names=feature_columns, class_names=["Reject", "Approve"], filled=True, rounded=True, fontsize=6
)
plt.title("Decision Tree Visualization - Loan Approval Rules", fontsize=16)
plt.savefig(f"{ARTIFACT_FOLDER}/decision_tree.png", dpi=300, bbox_inches="tight")
print("✅ Decision tree saved: decision_tree.png")

# متن کامل

tree_text = export_text(model, feature_names=feature_columns)

with open(f"{ARTIFACT_FOLDER}/decision_tree_full.txt", "w", encoding="utf-8") as f:
    f.write(tree_text)
print("✅ Full decision tree saved: decision_tree_full.txt")

# آمار درخت
n_nodes = model.tree_.node_count
depth = model.tree_.max_depth
n_leaves = model.tree_.n_leaves
print(f"\n📊 Tree Statistics:")
print(f"   Total nodes: {n_nodes}")
print(f"   Max depth: {depth}")
print(f"   Total leaves: {n_leaves}")

# ============================================================================
# Step 10: Model Evaluation
# ============================================================================
print("\n" + "=" * 70)
print("Step 10: Model Evaluation")
print("=" * 70)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"🎯 Overall Accuracy: {accuracy * 100:.1f}%")

cm = confusion_matrix(y_test, y_pred)
print("\n📊 Confusion Matrix:")
print(f"                 Prediction")
print(f"              Reject  Approve")
print(f"Actual Reject  {cm[0, 0]:5d}   {cm[0, 1]:5d}")
print(f"Actual Approve {cm[1, 0]:5d}   {cm[1, 1]:5d}")

tn, fp, fn, tp = cm.ravel()
print(f"\n📈 Detailed Performance:")
print(f"   Reject Class Accuracy: {tn / (tn + fp) * 100:.1f}%")
print(f"   Approve Class Accuracy: {tp / (tp + fn) * 100:.1f}%")

print("\n📋 Classification Report:")
print(classification_report(y_test, y_pred, target_names=["Reject", "Approve"]))

# ============================================================================
# Step 11: Feature Importance
# ============================================================================
print("\n" + "=" * 70)
print("Step 11: Feature Importance")
print("=" * 70)

feature_importance = pd.DataFrame({"Feature": feature_columns, "Importance": model.feature_importances_}).sort_values(
    "Importance", ascending=False
)

print("\n🔥 Most Important Features (Top 5):")
for i, row in feature_importance.head(5).iterrows():
    print(f"   {row['Feature']}: {row['Importance']:.4f}")

# Plot
plt.figure(figsize=(10, 6))
plt.barh(feature_importance.head(8)["Feature"], feature_importance.head(8)["Importance"], color="#339af0")
plt.xlabel("Importance")
plt.title("Feature Importance - Decision Tree", fontsize=14)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(f"{ARTIFACT_FOLDER}/feature_importance.png", dpi=150)
print("✅ Feature importance plot saved: feature_importance.png")

# ============================================================================
# Step 12: Save Model (No scaler needed)
# ============================================================================
print("\n" + "=" * 70)
print("Step 12: Save Model")
print("=" * 70)

model_package = {
    "model": model,
    "employment_encoder": le_employment,
    "purpose_encoder": le_purpose,
    "features": feature_columns,
    "performance": {"accuracy": accuracy, "confusion_matrix": cm.tolist()},
}

joblib.dump(model_package, f"{ARTIFACT_FOLDER}/loan_model.pkl")
print("✅ Model saved: loan_model.pkl")

# ============================================================================
# Step 13: Test with a New Customer (No scaling)
# ============================================================================
print("\n" + "=" * 70)
print("Step 13: Test Model with a New Customer")
print("=" * 70)

new_customer = pd.DataFrame(
    {
        "age": [35],
        "dependents": [2],
        "employment_years": [8],
        "monthly_income": [25000000],
        "credit_score": [720],
        "loan_amount": [80000000],
        "loan_term_months": [36],
        "has_other_loans": [0],
        "late_payments_last_year": [0],
        "marital_num": [1],
        "employment_num": [le_employment.transform(["کارمند"])[0]],
        "purpose_num": [le_purpose.transform(["مسکن"])[0]],
    }
)

# بدون scaling - مستقیماً پیش‌بینی
prediction = model.predict(new_customer)[0]
probability = model.predict_proba(new_customer)[0]

print("📝 New Customer Details:")
print(f"   Age: 35 years")
print(f"   Income: 25,000,000 Toman")
print(f"   Credit Score: 720")

print(f"\n🎯 Prediction Result:")
if prediction == 1:
    print(f"   ✅ Loan Approved")
else:
    print(f"   ❌ Loan Rejected")

print(f"\n📊 Approval Probability: {probability[1] * 100:.1f}%")

# ============================================================================
# Final Summary
# ============================================================================
print("\n" + "=" * 70)
print("📝 Final Summary")
print("=" * 70)

print(f"""
✅ Final Results:
- Overall Accuracy: {accuracy * 100:.1f}%
- Approve Class Accuracy: {tp / (tp + fn) * 100:.1f}%
- Reject Class Accuracy: {tn / (tn + fp) * 100:.1f}%

📁 Output Files:
- eda_plots.png : Exploratory Data Analysis plots
- decision_tree.png : Visualized decision tree
- decision_tree_full.txt : Full tree as text
- feature_importance.png : Feature importance visualization
- loan_model.pkl : Final trained model

💡 Key Takeaways:
- Decision Tree is easy to understand
- NO scaling needed (Decision Tree only compares values)
- Encoding IS required (model needs numbers)
- You can see exact decision rules in the tree

💾 Model file: loan_model.pkl
""")

print("=" * 70)
print("✅ Training Complete - Model Ready for Production")
print("=" * 70)
