"""
model.py — ML risk assessment engine with ensemble model and disease classification.

Provides:
    • predict_risk()           — simple score (backward compat)
    • assess_risk_advanced()   — full assessment with confidence,
                                  feature contributions, and anomalies
    • classify_disease()       — disease category classification with probabilities
"""

import os
import numpy as np
import joblib

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_DIR, "model.pkl")
ANOMALY_PATH = os.path.join(_DIR, "anomaly_model.pkl")
DISEASE_PATH = os.path.join(_DIR, "disease_classifier.pkl")
SCALER_PATH = os.path.join(_DIR, "scaler.pkl")

_risk_model = None
_anomaly_model = None
_disease_model = None
_scaler = None

FEATURE_NAMES = [
    "heart_rate", "glucose", "steps", "sleep_hours",
    "age", "bmi", "exercise_minutes", "calorie_intake"
]

DISEASE_LABELS = ["Normal", "Pre-Diabetic", "Diabetic", "High Cardiovascular Risk"]

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
        model_type = type(_risk_model).__name__
        print(f"🧠 Risk model loaded ({model_type})")
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


def _load_disease_model():
    global _disease_model
    if _disease_model is None:
        if not os.path.exists(DISEASE_PATH):
            print("⚠️  Disease classifier not found — using rule-based fallback")
            return None
        _disease_model = joblib.load(DISEASE_PATH)
        print("🏥 Disease classifier loaded")
    return _disease_model


def _load_scaler():
    global _scaler
    if _scaler is None:
        if not os.path.exists(SCALER_PATH):
            print("⚠️  Scaler not found — using unscaled features")
            return None
        _scaler = joblib.load(SCALER_PATH)
        print("📐 Feature scaler loaded")
    return _scaler


def _prepare_features(heart_rate, glucose, steps, sleep_hours,
                       age=35, bmi=25.0, exercise_minutes=30, calorie_intake=2200):
    """Prepare and scale feature vector."""
    raw = np.array([[
        heart_rate, glucose, steps, sleep_hours,
        age, bmi, exercise_minutes, calorie_intake
    ]])
    scaler = _load_scaler()
    if scaler is not None:
        return scaler.transform(raw), raw
    return raw, raw


def _rule_based_disease_label(
    heart_rate: float,
    glucose: float,
    age: int,
    bmi: float,
) -> str:
    """Clinical rule-based disease label for safety override."""
    if glucose >= 126:
        return "Diabetic"
    if glucose >= 100:
        return "Pre-Diabetic"
    if heart_rate > 90 and (bmi >= 28 or age >= 50):
        return "High Cardiovascular Risk"
    return "Normal"


def _severity_rank(label: str) -> int:
    """Higher number means more severe disease state."""
    ranks = {
        "Normal": 0,
        "Pre-Diabetic": 1,
        "High Cardiovascular Risk": 2,
        "Diabetic": 3,
    }
    return ranks.get(label, 0)


# ---------------------------------------------------------------------------
# Simple prediction (backward compatibility for /predict & live dashboard)
# ---------------------------------------------------------------------------

def predict_risk(heart_rate: float, glucose: float, steps: int, sleep_hours: float) -> float:
    """
    Quick risk score (0-100) using only 4 core vitals.
    Fills defaults for the extra 4 features the model expects.
    """
    model = _load_risk_model()
    features, _ = _prepare_features(heart_rate, glucose, steps, sleep_hours)
    score = model.predict(features)[0]
    return round(float(np.clip(score, 0, 100)), 1)


# ---------------------------------------------------------------------------
# Disease Classification (NEW)
# ---------------------------------------------------------------------------

def classify_disease(
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
    Classify patient into disease categories with probabilities.

    Returns:
        {
            "classification": "Normal" | "Pre-Diabetic" | "Diabetic" | "High Cardiovascular Risk",
            "confidence": float (0-1),
            "probabilities": { "Normal": 0.65, "Pre-Diabetic": 0.20, ... },
            "method": "ml" | "rule-based"
        }
    """
    disease_model = _load_disease_model()

    if disease_model is not None:
        features, _ = _prepare_features(
            heart_rate, glucose, steps, sleep_hours,
            age, bmi, exercise_minutes, calorie_intake
        )
        prediction = int(disease_model.predict(features)[0])
        probas = disease_model.predict_proba(features)[0]

        # Robust mapping using the classifier's classes_ order.
        label_map = {
            int(cls): DISEASE_LABELS[idx]
            for idx, cls in enumerate(disease_model.classes_)
        }
        classification = label_map.get(prediction, "Normal")

        proba_dict = {label: 0.0 for label in DISEASE_LABELS}
        for idx, cls in enumerate(disease_model.classes_):
            label = label_map.get(int(cls), "Normal")
            proba_dict[label] = round(float(probas[idx]), 3)

        confidence = float(max(probas))

        # Clinical rule-based safety override if model output appears too conservative.
        rule_label = _rule_based_disease_label(heart_rate, glucose, age, bmi)
        if _severity_rank(rule_label) > _severity_rank(classification):
            classification = rule_label
            confidence = max(confidence, 0.75)
            proba_dict[classification] = max(proba_dict.get(classification, 0.0), 0.65)
            total = sum(proba_dict.values())
            if total > 0:
                for key in proba_dict:
                    proba_dict[key] = round(proba_dict[key] / total, 3)

        return {
            "classification": classification,
            "confidence": round(confidence, 3),
            "probabilities": proba_dict,
            "method": "ml",
        }

    # ── Rule-based fallback (ADA / AHA clinical thresholds) ──
    if glucose >= 126:
        classification = "Diabetic"
        confidence = 0.85
    elif glucose >= 100:
        classification = "Pre-Diabetic"
        confidence = 0.75
    elif bmi >= 28 and age >= 40:
        classification = "Pre-Diabetic"
        confidence = 0.60
    elif heart_rate > 90 and (bmi >= 27 or age >= 50):
        classification = "High Cardiovascular Risk"
        confidence = 0.60
    else:
        classification = "Normal"
        confidence = 0.80

    return {
        "classification": classification,
        "confidence": confidence,
        "probabilities": {label: 0.0 for label in DISEASE_LABELS},  # not available rule-based
        "method": "rule-based",
    }


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
            "anomalies": [ { "vital", "value", "severity", "message" }, ... ],
            "disease_classification": { ... }
        }
    """
    risk_model = _load_risk_model()
    anomaly_model = _load_anomaly_model()

    features, raw_features = _prepare_features(
        heart_rate, glucose, steps, sleep_hours,
        age, bmi, exercise_minutes, calorie_intake
    )

    # ── Risk score ──
    score = float(np.clip(risk_model.predict(features)[0], 0, 100))

    # ── Confidence from sub-model variance (ensemble) ──
    try:
        # For VotingRegressor, get predictions from each sub-model
        sub_preds = []
        for name, est in risk_model.named_estimators_.items():
            sub_preds.append(est.predict(features)[0])
        sub_preds = np.array(sub_preds)
        pred_std = float(np.std(sub_preds))
        pred_mean = float(np.mean(sub_preds))
        confidence = 1.0 - min(1.0, pred_std / max(pred_mean, 1.0))
        confidence = max(0.5, min(0.99, confidence))
    except Exception:
        # Fallback: try tree-based variance for single RF model
        try:
            tree_preds = np.array([t.predict(features)[0] for t in risk_model.estimators_])
            pred_std = float(np.std(tree_preds))
            pred_mean = float(np.mean(tree_preds))
            confidence = 1.0 - min(1.0, pred_std / max(pred_mean, 1.0))
            confidence = max(0.5, min(0.99, confidence))
        except Exception:
            confidence = 0.75

    # ── Feature contributions ──
    try:
        # For VotingRegressor, average importances from sub-models
        rf_imp = risk_model.named_estimators_["rf"].feature_importances_
        gbr_imp = risk_model.named_estimators_["gbr"].feature_importances_
        importances = (rf_imp + gbr_imp) / 2
    except Exception:
        try:
            importances = risk_model.feature_importances_
        except Exception:
            importances = np.ones(len(FEATURE_NAMES)) / len(FEATURE_NAMES)

    feature_values = raw_features[0]
    feature_ranges = {
        "heart_rate": (55, 130), "glucose": (70, 220), "steps": (0, 15000),
        "sleep_hours": (3, 10), "age": (18, 85), "bmi": (15, 50),
        "exercise_minutes": (0, 90), "calorie_intake": (1200, 3500)
    }
    weighted_contributions = {}
    for i, name in enumerate(FEATURE_NAMES):
        lo, hi = feature_ranges[name]
        mid = (lo + hi) / 2
        extremity = abs(feature_values[i] - mid) / ((hi - lo) / 2) if hi != lo else 0
        weighted_contributions[name] = importances[i] * (0.5 + 0.5 * extremity)

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
        is_anomaly = anomaly_model.predict(features)[0]
        anomaly_score = -anomaly_model.score_samples(features)[0]
        if is_anomaly == -1:
            anomalies.append({
                "vital": "overall",
                "value": round(anomaly_score, 3),
                "severity": "warning",
                "message": f"Vital sign combination is statistically unusual (anomaly score: {anomaly_score:.2f})"
            })

    # ── Disease classification ──
    disease = classify_disease(
        heart_rate, glucose, steps, sleep_hours,
        age, bmi, exercise_minutes, calorie_intake
    )

    return {
        "risk_score": round(score, 1),
        "risk_level": risk_level,
        "confidence": round(confidence, 3),
        "feature_contributions": feature_contributions,
        "anomalies": anomalies,
        "disease_classification": disease,
    }
