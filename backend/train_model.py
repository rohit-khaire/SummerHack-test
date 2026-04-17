"""
train_model.py — Trains risk prediction and anomaly detection models
using the PIMA Indians Diabetes dataset as foundation, augmented with
synthetic vitals and lifestyle features for the Digital Twin system.

The PIMA dataset provides clinically validated relationships between
glucose, BMI, age, and diabetes outcomes — grounding our model in
real epidemiological data rather than arbitrary synthetic formulas.

Run once:  python train_model.py
Produces:  model.pkl, anomaly_model.pkl
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor, IsolationForest, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. Load PIMA Diabetes Dataset (bundled as CSV)
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
    # (glucose, blood_pressure, skin_thickness, insulin, bmi can't be 0)
    for col_idx in [1, 2, 3, 4, 5]:
        data[data[:, col_idx] == 0, col_idx] = np.nan

    return data


# ---------------------------------------------------------------------------
# 2. Build training dataset (PIMA-grounded + synthetic augmentation)
# ---------------------------------------------------------------------------

print("=" * 60)
print("🏥 Digital Twin — Model Training Pipeline")
print("=" * 60)

pima_data = load_pima()

N_SYNTHETIC = 4000
N_TOTAL = N_SYNTHETIC + (len(pima_data) if pima_data is not None else 0)

# Arrays to fill
all_heart_rate = []
all_glucose = []
all_steps = []
all_sleep_hours = []
all_age = []
all_bmi = []
all_exercise_minutes = []
all_calorie_intake = []
all_risk = []

# ── A. Convert PIMA records into Digital Twin features ──
if pima_data is not None:
    pima_count = 0
    for row in pima_data:
        glucose_val = row[1]
        bp = row[2]
        bmi_val = row[5]
        age_val = row[7]
        outcome = row[8]  # 1 = diabetic, 0 = healthy

        # Skip rows with NaN in critical fields
        if np.isnan(glucose_val) or np.isnan(bmi_val) or np.isnan(age_val):
            continue

        # Derive realistic vitals from PIMA data
        # Heart rate: correlates with blood pressure and age
        bp_val = bp if not np.isnan(bp) else 72.0
        hr = 60 + (bp_val - 60) * 0.4 + (age_val - 25) * 0.2 + np.random.normal(0, 5)
        hr = np.clip(hr, 55, 130)

        # Steps: inversely correlated with BMI and age
        base_steps = 8000 - (bmi_val - 22) * 200 - (age_val - 30) * 40
        steps_val = np.clip(base_steps + np.random.normal(0, 1500), 500, 15000)

        # Sleep: slightly affected by age and diabetes status
        sleep_val = 7.0 - outcome * 0.5 - max(0, age_val - 50) * 0.03 + np.random.normal(0, 0.8)
        sleep_val = np.clip(sleep_val, 3.5, 9.5)

        # Exercise: inversely correlated with BMI
        exercise_val = max(0, 45 - (bmi_val - 22) * 2 + np.random.normal(0, 15))
        exercise_val = np.clip(exercise_val, 0, 90)

        # Calories: correlated with BMI
        cal_val = 1800 + (bmi_val - 22) * 50 + np.random.normal(0, 200)
        cal_val = np.clip(cal_val, 1200, 3500)

        # Risk score from PIMA outcome + continuous features
        # Diabetic patients (outcome=1) have higher baseline risk
        # But risk is a continuous score, not binary
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
            + outcome * 12  # diabetic diagnosis adds base risk
            - np.clip(exercise_val / 60, 0, 1) * 6
        )
        risk_val = np.clip(risk_val + np.random.normal(0, 2), 0, 100)

        all_heart_rate.append(hr)
        all_glucose.append(glucose_val)
        all_steps.append(steps_val)
        all_sleep_hours.append(sleep_val)
        all_age.append(age_val)
        all_bmi.append(bmi_val)
        all_exercise_minutes.append(exercise_val)
        all_calorie_intake.append(cal_val)
        all_risk.append(risk_val)
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

# Non-linear risk formula matching PIMA-grounded logic
syn_glucose_risk = np.clip((syn_glucose - 80) / 140, 0, 1) ** 1.5
syn_hr_risk = np.clip((syn_hr - 60) / 70, 0, 1)
syn_activity_risk = np.clip((8000 - syn_steps) / 8000, 0, 1)
syn_sleep_risk = np.clip((7 - syn_sleep) / 3.5, 0, 1)
syn_age_risk = np.clip((syn_age - 25) / 50, 0, 1)
syn_bmi_risk = np.clip((syn_bmi - 22) / 18, 0, 1)
syn_exercise_benefit = np.clip(syn_exercise / 60, 0, 1)
syn_cal_risk = np.clip((syn_calories - 2000) / 1500, 0, 1)

# Interaction terms
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

all_heart_rate.extend(syn_hr)
all_glucose.extend(syn_glucose)
all_steps.extend(syn_steps)
all_sleep_hours.extend(syn_sleep)
all_age.extend(syn_age)
all_bmi.extend(syn_bmi)
all_exercise_minutes.extend(syn_exercise)
all_calorie_intake.extend(syn_calories)
all_risk.extend(syn_risk)

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
y = np.array(all_risk)

print(f"\n📊 Total training samples: {len(y)}")
print(f"   Risk range: {y.min():.1f} – {y.max():.1f}")
print(f"   Risk mean:  {y.mean():.1f} ± {y.std():.1f}")

# ---------------------------------------------------------------------------
# 4. Train / test split & RISK MODEL
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\n🔧 Training risk model (RandomForestRegressor)…")
risk_model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)
risk_model.fit(X_train, y_train)

preds = risk_model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print(f"✅ Risk model trained!")
print(f"   Samples: {len(X_train)} train / {len(X_test)} test")
print(f"   MAE  = {mae:.2f}")
print(f"   R²   = {r2:.4f}")

# Feature importance
importances = risk_model.feature_importances_
print("\n📊 Feature importances:")
for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"   {name:20s} {imp:.3f} {bar}")

# ---------------------------------------------------------------------------
# 5. ANOMALY DETECTION MODEL
# ---------------------------------------------------------------------------
print("\n🔧 Training anomaly detector (IsolationForest)…")
anomaly_model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)
anomaly_model.fit(X_train)
print("✅ Anomaly detector trained!")

# ---------------------------------------------------------------------------
# 6. Save models
# ---------------------------------------------------------------------------
joblib.dump(risk_model, "model.pkl")
joblib.dump(anomaly_model, "anomaly_model.pkl")

# Save metadata
metadata = {
    "total_samples": len(y),
    "pima_samples": pima_count if pima_data is not None else 0,
    "synthetic_samples": N_SYNTHETIC,
    "features": feature_names,
    "mae": round(mae, 3),
    "r2": round(r2, 4),
    "risk_range": [round(y.min(), 1), round(y.max(), 1)],
}
joblib.dump(metadata, "model_metadata.pkl")

print(f"\n💾 Saved: model.pkl, anomaly_model.pkl, model_metadata.pkl")
print(f"   Dataset: {metadata['pima_samples']} PIMA + {N_SYNTHETIC} synthetic = {len(y)} total")
print("=" * 60)
