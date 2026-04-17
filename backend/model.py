"""
model.py — ML risk assessment engine.

Provides:
    • predict_risk()           — simple score (backward compat)
    • assess_risk_advanced()   — full assessment with confidence,
                                  feature contributions, and anomalies
"""

import os
import math
import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_DIR, "model.pkl")
ANOMALY_PATH = os.path.join(_DIR, "anomaly_model.pkl")

_risk_model = None
_anomaly_model = None

FEATURE_NAMES = [
    "heart_rate", "glucose", "steps", "sleep_hours",
    "age", "bmi", "exercise_minutes", "calorie_intake"
]

# Thresholds for anomaly alerts (clinically meaningful)
VITAL_THRESHOLDS = {
    "heart_rate":  {"low": 50, "high": 110, "critical_high": 130, "unit": "BPM"},
    "glucose":     {"low": 60, "high": 160, "critical_high": 200, "unit": "mg/dL"},
    "steps":       {"low": 1000, "high": 99999, "critical_high": 99999, "unit": "steps"},
    "sleep_hours": {"low": 4.5, "high": 99, "critical_high": 99, "unit": "hrs"},
}


def _load_risk_model():
    global _risk_model
    if _risk_model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run: python train_model.py")
        _risk_model = joblib.load(MODEL_PATH)
        print("🧠 Risk model loaded")
    return _risk_model


def _load_anomaly_model():
    global _anomaly_model
    if _anomaly_model is None:
        if not os.path.exists(ANOMALY_PATH):
            print("⚠️  Anomaly model not found — anomaly detection disabled")
            return None
        _anomaly_model = joblib.load(ANOMALY_PATH)
        print("🔍 Anomaly model loaded")
    return _anomaly_model


# ---------------------------------------------------------------------------
# Simple prediction (backward compatibility for /predict & live dashboard)
# ---------------------------------------------------------------------------

def predict_risk(heart_rate: float, glucose: float, steps: int, sleep_hours: float) -> float:
    """
    Quick risk score (0-100) using only 4 core vitals.
    Fills defaults for the extra 4 features the model expects.
    """
    model = _load_risk_model()
    features = np.array([[
        heart_rate, glucose, steps, sleep_hours,
        35,     # default age
        25.0,   # default BMI
        30,     # default exercise_minutes
        2200    # default calorie_intake
    ]])
    score = model.predict(features)[0]
    return round(float(np.clip(score, 0, 100)), 1)


# ---------------------------------------------------------------------------
# Advanced risk assessment
# ---------------------------------------------------------------------------

def assess_risk_advanced(
    heart_rate: float,
    glucose: float,
    steps: int,
    sleep_hours: float,
    age: int = 35,
    bmi: float = 25.0,
    exercise_minutes: float = 30,
    calorie_intake: float = 2200,
) -> dict:
    """
    Full risk assessment with confidence interval, feature contributions,
    per-vital anomaly detection, and risk level classification.

    Returns:
        {
            "risk_score": float,
            "risk_level": "Low" | "Moderate" | "High" | "Critical",
            "confidence": float (0-1),
            "feature_contributions": { feature_name: pct, ... },
            "anomalies": [ { "vital", "value", "severity", "message" }, ... ]
        }
    """
    risk_model = _load_risk_model()
    anomaly_model = _load_anomaly_model()

    features = np.array([[
        heart_rate, glucose, steps, sleep_hours,
        age, bmi, exercise_minutes, calorie_intake
    ]])

    # ── Risk score ──
    score = float(np.clip(risk_model.predict(features)[0], 0, 100))

    # ── Confidence from tree variance ──
    tree_preds = np.array([t.predict(features)[0] for t in risk_model.estimators_])
    pred_std = float(np.std(tree_preds))
    pred_mean = float(np.mean(tree_preds))
    # Confidence = 1 - (relative spread); clamp to [0.5, 0.99]
    confidence = 1.0 - min(1.0, pred_std / max(pred_mean, 1.0))
    confidence = max(0.5, min(0.99, confidence))

    # ── Feature contributions (from feature_importances_) ──
    importances = risk_model.feature_importances_
    feature_values = features[0]
    # Weight importances by how "extreme" each feature is
    feature_ranges = {
        "heart_rate": (55, 130), "glucose": (70, 220), "steps": (0, 15000),
        "sleep_hours": (3, 10), "age": (18, 85), "bmi": (15, 50),
        "exercise_minutes": (0, 90), "calorie_intake": (1200, 3500)
    }
    weighted_contributions = {}
    for i, name in enumerate(FEATURE_NAMES):
        lo, hi = feature_ranges[name]
        # How extreme is this value? (0 = midpoint, 1 = extreme)
        mid = (lo + hi) / 2
        extremity = abs(feature_values[i] - mid) / ((hi - lo) / 2) if hi != lo else 0
        weighted_contributions[name] = importances[i] * (0.5 + 0.5 * extremity)

    # Normalize to percentages
    total = sum(weighted_contributions.values())
    feature_contributions = {
        k: round(v / total * 100, 1) if total > 0 else 0
        for k, v in weighted_contributions.items()
    }

    # ── Risk level ──
    if score >= 75:
        risk_level = "Critical"
    elif score >= 55:
        risk_level = "High"
    elif score >= 35:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # ── Anomaly detection ──
    anomalies = []

    # 1) Threshold-based clinical anomalies
    vital_values = {
        "heart_rate": heart_rate,
        "glucose": glucose,
        "steps": steps,
        "sleep_hours": sleep_hours,
    }
    for vital, value in vital_values.items():
        thresholds = VITAL_THRESHOLDS[vital]
        if value >= thresholds.get("critical_high", float('inf')):
            anomalies.append({
                "vital": vital,
                "value": value,
                "severity": "critical",
                "message": f"{vital.replace('_', ' ').title()} {value} {thresholds['unit']} is critically high (>{thresholds['critical_high']})"
            })
        elif value >= thresholds["high"]:
            anomalies.append({
                "vital": vital,
                "value": value,
                "severity": "warning",
                "message": f"{vital.replace('_', ' ').title()} {value} {thresholds['unit']} is elevated (>{thresholds['high']})"
            })
        elif value <= thresholds["low"]:
            anomalies.append({
                "vital": vital,
                "value": value,
                "severity": "warning",
                "message": f"{vital.replace('_', ' ').title()} {value} {thresholds['unit']} is below normal (<{thresholds['low']})"
            })

    # 2) Isolation Forest statistical anomaly
    if anomaly_model is not None:
        is_anomaly = anomaly_model.predict(features)[0]  # -1 = anomaly
        anomaly_score = -anomaly_model.score_samples(features)[0]
        if is_anomaly == -1:
            anomalies.append({
                "vital": "overall",
                "value": round(anomaly_score, 3),
                "severity": "warning",
                "message": f"Vital sign combination is statistically unusual (anomaly score: {anomaly_score:.2f})"
            })

    return {
        "risk_score": round(score, 1),
        "risk_level": risk_level,
        "confidence": round(confidence, 3),
        "feature_contributions": feature_contributions,
        "anomalies": anomalies,
    }
