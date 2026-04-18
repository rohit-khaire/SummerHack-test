"""
train_model.py — Trains ensemble risk prediction, disease classification,
and anomaly detection models using PIMA Diabetes dataset + synthetic data.

Models produced:
    • model.pkl           — VotingRegressor (RF + GBR) for risk score 0-100
    • disease_classifier.pkl — GradientBoostingClassifier for disease categories
    • anomaly_model.pkl   — IsolationForest for statistical outlier detection
    • scaler.pkl          — StandardScaler for feature normalization
    • model_metadata.pkl  — Training metrics and metadata

Run once:  python train_model.py
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    IsolationForest,
    GradientBoostingClassifier,
    VotingRegressor,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. Load PIMA Diabetes Dataset
# ---------------------------------------------------------------------------

PIMA_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
PIMA_COLS = [
    "pregnancies", "glucose", "blood_pressure", "skin_thickness",
    "insulin", "bmi", "diabetes_pedigree", "age", "outcome"
]

def load_pima():
    """Load PIMA dataset from URL or local cache."""
    cache_path = os.path.join(os.path.dirname(__file__), "pima_cache.csv")

    if os.path.exists(cache_path):
        print("📂 Loading PIMA dataset from cache…")
        data = np.genfromtxt(cache_path, delimiter=",", skip_header=0)
    else:
        print("🌐 Downloading PIMA Diabetes Dataset…")
        try:
            import urllib.request
            urllib.request.urlretrieve(PIMA_URL, cache_path)
            data = np.genfromtxt(cache_path, delimiter=",")
            print(f"   Saved {len(data)} records to {cache_path}")
        except Exception as e:
            print(f"⚠️  Could not download PIMA dataset: {e}")
            print("   Falling back to synthetic-only data")
            return None

    # Replace zeros with NaN for clinically impossible zero values
    for col_idx in [1, 2, 3, 4, 5]:
        data[data[:, col_idx] == 0, col_idx] = np.nan

    return data


# ---------------------------------------------------------------------------
# 2. Build training dataset
# ---------------------------------------------------------------------------

print("=" * 60)
print("🏥 Digital Twin — Model Training Pipeline v4.0")
print("   Ensemble (RF + GBR) + Disease Classifier")
print("=" * 60)

pima_data = load_pima()

N_SYNTHETIC = 4000
N_TOTAL = N_SYNTHETIC + (len(pima_data) if pima_data is not None else 0)

# Arrays for risk regression
all_heart_rate = []
all_glucose = []
all_steps = []
all_sleep_hours = []
all_age = []
all_bmi = []
all_exercise_minutes = []
all_calorie_intake = []
all_risk = []

# Arrays for disease classification
all_disease_label = []  # 0=Normal, 1=Pre-Diabetic, 2=Diabetic, 3=High Cardiovascular Risk

# ── A. Convert PIMA records into Digital Twin features ──
pima_count = 0
if pima_data is not None:
    for row in pima_data:
        glucose_val = row[1]
        bp = row[2]
        bmi_val = row[5]
        age_val = row[7]
        outcome = row[8]

        if np.isnan(glucose_val) or np.isnan(bmi_val) or np.isnan(age_val):
            continue

        # Derive realistic vitals from PIMA data
        bp_val = bp if not np.isnan(bp) else 72.0
        hr = 60 + (bp_val - 60) * 0.4 + (age_val - 25) * 0.2 + np.random.normal(0, 5)
        hr = np.clip(hr, 55, 130)

        base_steps = 8000 - (bmi_val - 22) * 200 - (age_val - 30) * 40
        steps_val = np.clip(base_steps + np.random.normal(0, 1500), 500, 15000)

        sleep_val = 7.0 - outcome * 0.5 - max(0, age_val - 50) * 0.03 + np.random.normal(0, 0.8)
        sleep_val = np.clip(sleep_val, 3.5, 9.5)

        exercise_val = max(0, 45 - (bmi_val - 22) * 2 + np.random.normal(0, 15))
        exercise_val = np.clip(exercise_val, 0, 90)

        cal_val = 1800 + (bmi_val - 22) * 50 + np.random.normal(0, 200)
        cal_val = np.clip(cal_val, 1200, 3500)

        # Risk score (continuous)
        glucose_risk = np.clip((glucose_val - 80) / 140, 0, 1) ** 1.5
        bmi_risk = np.clip((bmi_val - 22) / 18, 0, 1)
        age_risk = np.clip((age_val - 25) / 50, 0, 1)
        activity_risk = np.clip((8000 - steps_val) / 8000, 0, 1)
        sleep_risk = np.clip((7 - sleep_val) / 3.5, 0, 1)

        risk_val = (
            glucose_risk * 32
            + (hr - 60) / 70 * 18
            + activity_risk * 14
            + sleep_risk * 10
            + age_risk * 8
            + bmi_risk * 8
            + outcome * 12
            - np.clip(exercise_val / 60, 0, 1) * 6
        )
        risk_val = np.clip(risk_val + np.random.normal(0, 2), 0, 100)

        # Disease classification (ADA / AHA clinical thresholds)
        # ADA: Diabetic = fasting glucose ≥126, Pre-Diabetic = 100-125
        if outcome == 1 or glucose_val >= 126:
            disease_label = 2  # Diabetic
        elif glucose_val >= 100 or (bmi_val >= 28 and age_val >= 40):
            disease_label = 1  # Pre-Diabetic
        elif hr > 90 and (bmi_val >= 27 or age_val >= 50):
            disease_label = 3  # High Cardiovascular Risk
        else:
            disease_label = 0  # Normal

        all_heart_rate.append(hr)
        all_glucose.append(glucose_val)
        all_steps.append(steps_val)
        all_sleep_hours.append(sleep_val)
        all_age.append(age_val)
        all_bmi.append(bmi_val)
        all_exercise_minutes.append(exercise_val)
        all_calorie_intake.append(cal_val)
        all_risk.append(risk_val)
        all_disease_label.append(disease_label)
        pima_count += 1

    print(f"✅ Converted {pima_count} PIMA records to Digital Twin features")

# ── B. Generate synthetic augmentation data ──
print(f"🔧 Generating {N_SYNTHETIC} synthetic samples…")

syn_hr = np.random.uniform(55, 130, N_SYNTHETIC)
syn_glucose = np.random.uniform(70, 220, N_SYNTHETIC)
syn_steps = np.random.uniform(0, 15000, N_SYNTHETIC)
syn_sleep = np.random.uniform(3, 10, N_SYNTHETIC)
syn_age = np.random.uniform(18, 85, N_SYNTHETIC)
syn_bmi = np.clip(np.random.normal(26, 5, N_SYNTHETIC), 15, 50)
syn_exercise = np.random.uniform(0, 90, N_SYNTHETIC)
syn_calories = np.random.uniform(1200, 3500, N_SYNTHETIC)

# Non-linear risk formula
syn_glucose_risk = np.clip((syn_glucose - 80) / 140, 0, 1) ** 1.5
syn_hr_risk = np.clip((syn_hr - 60) / 70, 0, 1)
syn_activity_risk = np.clip((8000 - syn_steps) / 8000, 0, 1)
syn_sleep_risk = np.clip((7 - syn_sleep) / 3.5, 0, 1)
syn_age_risk = np.clip((syn_age - 25) / 50, 0, 1)
syn_bmi_risk = np.clip((syn_bmi - 22) / 18, 0, 1)
syn_exercise_benefit = np.clip(syn_exercise / 60, 0, 1)
syn_cal_risk = np.clip((syn_calories - 2000) / 1500, 0, 1)

syn_gluc_activity_interaction = syn_glucose_risk * syn_activity_risk
syn_sleep_hr_interaction = syn_sleep_risk * syn_hr_risk

syn_risk = (
    syn_glucose_risk * 30
    + syn_hr_risk * 18
    + syn_activity_risk * 14
    + syn_sleep_risk * 10
    + syn_age_risk * 8
    + syn_bmi_risk * 7
    + syn_gluc_activity_interaction * 8
    + syn_sleep_hr_interaction * 4
    - syn_exercise_benefit * 6
    + syn_cal_risk * 3
)
syn_risk += np.random.normal(0, 2.5, N_SYNTHETIC)
syn_risk = np.clip(syn_risk, 0, 100)

# Disease labels for synthetic data (ADA / AHA clinical thresholds)
syn_disease = np.zeros(N_SYNTHETIC, dtype=int)
for i in range(N_SYNTHETIC):
    if syn_glucose[i] >= 126:
        syn_disease[i] = 2  # Diabetic (ADA: fasting glucose ≥126)
    elif syn_glucose[i] >= 100 or (syn_bmi[i] >= 28 and syn_age[i] >= 40):
        syn_disease[i] = 1  # Pre-Diabetic (ADA: fasting glucose 100-125)
    elif syn_hr[i] > 90 and (syn_bmi[i] >= 27 or syn_age[i] >= 50):
        syn_disease[i] = 3  # High Cardiovascular Risk
    else:
        syn_disease[i] = 0  # Normal

all_heart_rate.extend(syn_hr)
all_glucose.extend(syn_glucose)
all_steps.extend(syn_steps)
all_sleep_hours.extend(syn_sleep)
all_age.extend(syn_age)
all_bmi.extend(syn_bmi)
all_exercise_minutes.extend(syn_exercise)
all_calorie_intake.extend(syn_calories)
all_risk.extend(syn_risk)
all_disease_label.extend(syn_disease)

# ---------------------------------------------------------------------------
# 3. Feature matrix
# ---------------------------------------------------------------------------
feature_names = [
    "heart_rate", "glucose", "steps", "sleep_hours",
    "age", "bmi", "exercise_minutes", "calorie_intake"
]
X = np.column_stack([
    all_heart_rate, all_glucose, all_steps, all_sleep_hours,
    all_age, all_bmi, all_exercise_minutes, all_calorie_intake
])
y_risk = np.array(all_risk)
y_disease = np.array(all_disease_label)

print(f"\n📊 Total training samples: {len(y_risk)}")
print(f"   Risk range: {y_risk.min():.1f} – {y_risk.max():.1f}")
print(f"   Risk mean:  {y_risk.mean():.1f} ± {y_risk.std():.1f}")
print(f"   Disease distribution: Normal={np.sum(y_disease==0)}, "
      f"Pre-Diabetic={np.sum(y_disease==1)}, Diabetic={np.sum(y_disease==2)}, "
      f"CardioRisk={np.sum(y_disease==3)}")

# ---------------------------------------------------------------------------
# 4. Feature Scaling
# ---------------------------------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------------------------------------------------------------------------
# 5. Train / test split & ENSEMBLE RISK MODEL
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_risk, test_size=0.2, random_state=42
)

print("\n🔧 Training ensemble risk model (RandomForest + GradientBoosting)…")

rf_model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
)

gbr_model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    min_samples_leaf=5,
    subsample=0.8,
    random_state=42,
)

ensemble_model = VotingRegressor(
    estimators=[("rf", rf_model), ("gbr", gbr_model)],
    n_jobs=-1,
)
ensemble_model.fit(X_train, y_train)

preds = ensemble_model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print(f"✅ Ensemble risk model trained!")
print(f"   Samples: {len(X_train)} train / {len(X_test)} test")
print(f"   MAE  = {mae:.2f}")
print(f"   R²   = {r2:.4f}")

# Feature importance (average of RF + GBR)
rf_imp = ensemble_model.named_estimators_["rf"].feature_importances_
gbr_imp = ensemble_model.named_estimators_["gbr"].feature_importances_
avg_importances = (rf_imp + gbr_imp) / 2

print("\n📊 Feature importances (ensemble average):")
for name, imp in sorted(zip(feature_names, avg_importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"   {name:20s} {imp:.3f} {bar}")

# ---------------------------------------------------------------------------
# 6. DISEASE CLASSIFICATION MODEL
# ---------------------------------------------------------------------------
print("\n🔧 Training disease classifier (GradientBoostingClassifier)…")

X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
    X_scaled, y_disease, test_size=0.2, random_state=42, stratify=y_disease
)

disease_model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    min_samples_leaf=10,
    subsample=0.8,
    random_state=42,
)
disease_model.fit(X_train_d, y_train_d)

disease_preds = disease_model.predict(X_test_d)
disease_accuracy = accuracy_score(y_test_d, disease_preds)

DISEASE_LABELS = ["Normal", "Pre-Diabetic", "Diabetic", "High Cardiovascular Risk"]
print(f"✅ Disease classifier trained!")
print(f"   Accuracy: {disease_accuracy:.4f}")
print("\n📊 Classification Report:")
print(classification_report(y_test_d, disease_preds, target_names=DISEASE_LABELS))

# ---------------------------------------------------------------------------
# 7. ANOMALY DETECTION MODEL
# ---------------------------------------------------------------------------
print("🔧 Training anomaly detector (IsolationForest)…")
anomaly_model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42,
    n_jobs=-1,
)
anomaly_model.fit(X_train)
print("✅ Anomaly detector trained!")

# ---------------------------------------------------------------------------
# 8. Save all models
# ---------------------------------------------------------------------------
model_dir = os.path.dirname(__file__) or "."

joblib.dump(ensemble_model, os.path.join(model_dir, "model.pkl"))
joblib.dump(disease_model, os.path.join(model_dir, "disease_classifier.pkl"))
joblib.dump(anomaly_model, os.path.join(model_dir, "anomaly_model.pkl"))
joblib.dump(scaler, os.path.join(model_dir, "scaler.pkl"))

# Save metadata
metadata = {
    "total_samples": len(y_risk),
    "pima_samples": pima_count if pima_data is not None else 0,
    "synthetic_samples": N_SYNTHETIC,
    "features": feature_names,
    "mae": round(mae, 3),
    "r2": round(r2, 4),
    "risk_range": [round(y_risk.min(), 1), round(y_risk.max(), 1)],
    "disease_accuracy": round(disease_accuracy, 4),
    "disease_labels": DISEASE_LABELS,
    "model_type": "VotingRegressor (RandomForest + GradientBoosting)",
    "ensemble_importances": {name: round(float(imp), 4) for name, imp in zip(feature_names, avg_importances)},
}
joblib.dump(metadata, os.path.join(model_dir, "model_metadata.pkl"))

print(f"\n💾 Saved: model.pkl, disease_classifier.pkl, anomaly_model.pkl, scaler.pkl, model_metadata.pkl")
print(f"   Dataset: {metadata['pima_samples']} PIMA + {N_SYNTHETIC} synthetic = {len(y_risk)} total")
print(f"   Ensemble R²: {r2:.4f} | MAE: {mae:.2f}")
print(f"   Disease accuracy: {disease_accuracy:.4f}")
print("=" * 60)
