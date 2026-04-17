"""
patient.py — Patient profile model and physiological modifiers.

Encapsulates demographics, pre-existing conditions, and derived
biomarkers (BMI) that influence simulation dynamics.
"""

from pydantic import BaseModel, Field
import math


# ---------------------------------------------------------------------------
# Patient profile schema
# ---------------------------------------------------------------------------

class PatientProfile(BaseModel):
    """Demographics and health conditions of the patient."""
    age: int = Field(default=35, ge=18, le=90, description="Patient age in years")
    weight_kg: float = Field(default=75.0, ge=30, le=250, description="Body weight (kg)")
    height_cm: float = Field(default=170.0, ge=100, le=230, description="Height (cm)")
    conditions: list[str] = Field(
        default=[],
        description="Pre-existing conditions: 'diabetes', 'hypertension', 'obesity'"
    )

    @property
    def bmi(self) -> float:
        """Body Mass Index = weight(kg) / height(m)²."""
        h_m = self.height_cm / 100.0
        return round(self.weight_kg / (h_m * h_m), 1)

    @property
    def bmi_category(self) -> str:
        b = self.bmi
        if b < 18.5:
            return "underweight"
        elif b < 25:
            return "normal"
        elif b < 30:
            return "overweight"
        else:
            return "obese"


# ---------------------------------------------------------------------------
# Physiological modifier calculations
# ---------------------------------------------------------------------------

def compute_modifiers(profile: PatientProfile) -> dict:
    """
    Derive physiological modifiers from the patient profile.

    These modifiers scale the simulation parameters to account for
    individual patient characteristics.

    Returns:
        dict with keys:
            - age_factor:       τ multiplier (older → slower adaptation)
            - glucose_floor:    minimum achievable glucose (mg/dL)
            - hr_floor:         minimum achievable resting HR (BPM)
            - bmi_penalty:      multiplicative risk uplift for high BMI
            - adaptation_rate:  overall speed of physiological adaptation
    """
    age = profile.age
    bmi = profile.bmi
    conditions = [c.lower().strip() for c in profile.conditions]

    # ── Age factor ──
    # Cellular adaptation slows ~2 % per year past age 30.
    # Young patients adapt faster; capped at 0.6× (age 18) and 2.2× (age 90).
    age_factor = max(0.6, 1.0 + 0.02 * (age - 30))

    # ── Glucose floor ──
    # Healthy baseline: ~85 mg/dL fasting.
    # Diabetics: +25 mg/dL due to chronic insulin resistance.
    # Overweight/obese: +5–10 mg/dL due to adiposity-related IR.
    glucose_floor = 85.0
    if "diabetes" in conditions:
        glucose_floor += 25.0
    if bmi >= 30:
        glucose_floor += 10.0
    elif bmi >= 25:
        glucose_floor += 5.0

    # ── Heart rate floor ──
    # Healthy resting HR: ~62 BPM.
    # Hypertension: elevated sympathetic tone adds ~10 BPM.
    # Age: resting HR tends to rise slightly with age.
    hr_floor = 62.0
    if "hypertension" in conditions:
        hr_floor += 10.0
    hr_floor += max(0, (age - 40) * 0.15)  # +0.15 BPM per year past 40

    # ── BMI penalty for risk ──
    # Exponential uplift: BMI 25 → 1.0×, BMI 35 → ~1.3×, BMI 45 → ~1.7×
    bmi_penalty = 1.0
    if bmi > 25:
        bmi_penalty = 1.0 + 0.03 * (bmi - 25)

    # ── Overall adaptation rate ──
    # Inverse of age_factor; used as the 1/τ in exponential decay.
    adaptation_rate = 1.0 / age_factor

    return {
        "age_factor": round(age_factor, 3),
        "glucose_floor": round(glucose_floor, 1),
        "hr_floor": round(hr_floor, 1),
        "bmi_penalty": round(bmi_penalty, 3),
        "adaptation_rate": round(adaptation_rate, 4),
        "bmi": bmi,
        "bmi_category": profile.bmi_category,
        "has_diabetes": "diabetes" in conditions,
        "has_hypertension": "hypertension" in conditions,
    }
