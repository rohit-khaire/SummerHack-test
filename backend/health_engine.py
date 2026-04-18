"""
health_engine.py — Clinical decision support engine.

Provides:
    • compute_health_score()           — Composite 0-100 wellness metric
    • classify_patient_segment()       — Risk stratification
    • generate_recommendations()       — Personalized action plans
    • check_early_warnings()           — Real-time alert generation
    • generate_groq_recommendations()  — Structured AI-powered plan via Groq
    • compute_trend_intelligence()     — "Glucose increased 12% over 5 days"
    • compute_intervention_impact()    — "Exercise contributed 65% to improvement"
    • compute_stability_indicator()    — Stable vs Volatile classification
"""

import math
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ═══════════════════════════════════════════════════════════════════════════
# 1. COMPOSITE HEALTH SCORE (0-100, higher = healthier)
# ═══════════════════════════════════════════════════════════════════════════

def compute_health_score(
    heart_rate: float,
    glucose: float,
    steps: int,
    sleep_hours: float,
    age: int = 35,
    bmi: float = 25.0,
    exercise_minutes: float = 30,
) -> dict:
    """
    Compute a composite Health Score (0-100, higher = better).
    Based on AHA & WHO guidelines for optimal ranges.
    """
    # ── Component scores (each 0-100, higher = better) ──

    # Cardiovascular: optimal resting HR = 60-72 BPM (AHA)
    if heart_rate <= 72:
        cardio = 100
    elif heart_rate <= 85:
        cardio = 100 - (heart_rate - 72) * 2.5
    elif heart_rate <= 100:
        cardio = 68 - (heart_rate - 85) * 2.0
    else:
        cardio = max(0, 38 - (heart_rate - 100) * 1.5)

    # Metabolic: optimal fasting glucose = 70-100 mg/dL (ADA)
    if glucose <= 100:
        metabolic = 100
    elif glucose <= 125:
        metabolic = 100 - (glucose - 100) * 2.0
    elif glucose <= 180:
        metabolic = 50 - (glucose - 125) * 0.6
    else:
        metabolic = max(0, 17 - (glucose - 180) * 0.5)

    # Activity: WHO recommends 150+ min/week moderate exercise
    step_score = min(100, (steps / 10000) * 100)
    exercise_score = min(100, (exercise_minutes / 45) * 100)
    activity = (step_score * 0.5 + exercise_score * 0.5)

    # Sleep: optimal 7-9 hours (NSF)
    if 7 <= sleep_hours <= 9:
        sleep_score = 100
    elif 6 <= sleep_hours < 7:
        sleep_score = 80
    elif 5 <= sleep_hours < 6:
        sleep_score = 55
    elif sleep_hours > 9:
        sleep_score = 85
    else:
        sleep_score = max(0, 55 - (5 - sleep_hours) * 20)

    # Body composition: optimal BMI 18.5-24.9 (WHO)
    if 18.5 <= bmi <= 24.9:
        body = 100
    elif 25 <= bmi < 30:
        body = 100 - (bmi - 25) * 6
    elif bmi >= 30:
        body = max(0, 70 - (bmi - 30) * 4)
    else:
        body = max(0, 100 - (18.5 - bmi) * 10)

    # ── Weighted composite ──
    weights = {
        "cardiovascular": 0.22,
        "metabolic": 0.28,
        "activity": 0.20,
        "sleep": 0.15,
        "body_composition": 0.15,
    }
    components = {
        "cardiovascular": round(cardio, 1),
        "metabolic": round(metabolic, 1),
        "activity": round(activity, 1),
        "sleep": round(sleep_score, 1),
        "body_composition": round(body, 1),
    }

    health_score = sum(components[k] * weights[k] for k in weights)
    age_penalty = max(0, (age - 40) * 0.15)
    health_score = max(0, min(100, health_score - age_penalty))

    if health_score >= 85:
        grade = "A"
    elif health_score >= 70:
        grade = "B"
    elif health_score >= 55:
        grade = "C"
    elif health_score >= 40:
        grade = "D"
    else:
        grade = "F"

    sorted_components = sorted(components.items(), key=lambda x: x[1])
    weakest = sorted_components[0][0]
    strongest = sorted_components[-1][0]

    return {
        "health_score": round(health_score, 1),
        "grade": grade,
        "component_scores": components,
        "weakest_area": weakest,
        "strongest_area": strongest,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. PATIENT SEGMENTATION
# ═══════════════════════════════════════════════════════════════════════════

def classify_patient_segment(
    glucose: float,
    bmi: float,
    age: int,
    heart_rate: float,
    risk_score: float,
    conditions: list[str] = None,
) -> dict:
    """Classify patient into clinical risk segment based on ADA/AHA guidelines."""
    conditions = [c.lower() for c in (conditions or [])]
    risk_factors = []

    if glucose >= 200:
        risk_factors.append("Diabetic-range glucose (≥200 mg/dL)")
    elif glucose >= 140:
        risk_factors.append("Impaired glucose tolerance (140-199 mg/dL)")
    elif glucose >= 100:
        risk_factors.append("Pre-diabetic glucose (100-139 mg/dL)")

    if bmi >= 30:
        risk_factors.append(f"Obesity (BMI {bmi:.1f})")
    elif bmi >= 25:
        risk_factors.append(f"Overweight (BMI {bmi:.1f})")

    if heart_rate > 100:
        risk_factors.append(f"Tachycardia (HR {heart_rate:.0f} BPM)")

    if age >= 45:
        risk_factors.append(f"Age ≥45 (increased metabolic risk)")

    if "diabetes" in conditions:
        risk_factors.append("Diagnosed diabetes")
    if "hypertension" in conditions:
        risk_factors.append("Diagnosed hypertension")

    factor_count = len(risk_factors)

    if "diabetes" in conditions or glucose >= 200 or risk_score >= 70:
        segment = "High Risk"
        description = (
            "Multiple significant risk factors detected. "
            "Active clinical monitoring and lifestyle intervention strongly recommended."
        )
        color = "rose"
        monitoring = "Weekly vitals check, monthly physician review"
    elif glucose >= 100 or factor_count >= 3 or risk_score >= 45:
        segment = "Pre-Diabetic"
        description = (
            "Metabolic indicators suggest elevated risk for type 2 diabetes. "
            "Lifestyle modifications can significantly reduce progression risk."
        )
        color = "amber"
        monitoring = "Bi-weekly vitals check, quarterly physician review"
    elif factor_count >= 1 or risk_score >= 25:
        segment = "Moderate Risk"
        description = (
            "Some risk factors present but within manageable range. "
            "Maintain healthy habits and track trends over time."
        )
        color = "yellow"
        monitoring = "Monthly self-monitoring, annual physician check"
    else:
        segment = "Low Risk"
        description = (
            "Vital signs and metabolic markers are within healthy ranges. "
            "Continue current lifestyle to maintain excellent health."
        )
        color = "emerald"
        monitoring = "Quarterly self-monitoring, annual wellness check"

    return {
        "segment": segment,
        "segment_description": description,
        "segment_color": color,
        "risk_factors": risk_factors,
        "monitoring_frequency": monitoring,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def generate_recommendations(
    health_score: dict,
    segment: dict,
    baseline_vitals: dict,
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    age: int,
    bmi: float,
    conditions: list[str] = None,
) -> list[dict]:
    """Generate personalized, actionable health recommendations."""
    recs = []
    conditions = [c.lower() for c in (conditions or [])]
    glucose = baseline_vitals.get("glucose", 100)
    hr = baseline_vitals.get("heart_rate", 75)
    steps = baseline_vitals.get("steps", 5000)

    if exercise_minutes < 30:
        recs.append({
            "category": "exercise",
            "priority": "high",
            "title": "Increase Daily Movement",
            "description": (
                f"Currently at {exercise_minutes:.0f} min/day. WHO recommends 150 min/week "
                f"(~22 min/day) of moderate aerobic activity. Start with brisk walking "
                f"for 20-30 minutes daily and gradually increase intensity."
            ),
            "expected_impact": "5-15% glucose reduction, improved insulin sensitivity within 2 weeks",
        })
    elif exercise_minutes < 60:
        recs.append({
            "category": "exercise",
            "priority": "medium",
            "title": "Diversify Exercise Routine",
            "description": (
                f"Good baseline at {exercise_minutes:.0f} min/day. Add resistance training "
                f"2-3 times per week to improve glucose uptake by skeletal muscle."
            ),
            "expected_impact": "Additional 3-8% risk reduction with consistent resistance training",
        })

    if steps < 5000:
        recs.append({
            "category": "exercise",
            "priority": "high",
            "title": "Combat Sedentary Behavior",
            "description": (
                f"Only {steps:,} steps/day suggests a sedentary lifestyle. "
                f"Aim for 7,000-10,000 steps. Take walking meetings, use stairs."
            ),
            "expected_impact": "Each additional 2,000 steps/day reduces cardiovascular risk by ~8%",
        })

    if sleep_hours < 6:
        recs.append({
            "category": "sleep",
            "priority": "high",
            "title": "Address Sleep Deprivation",
            "description": (
                f"Sleeping {sleep_hours:.1f} hrs is critically low. Sleep deprivation impairs "
                f"glucose regulation, elevates cortisol, and increases appetite hormones."
            ),
            "expected_impact": "Improving to 7+ hours can reduce glucose by 10-20 mg/dL",
        })
    elif sleep_hours < 7:
        recs.append({
            "category": "sleep",
            "priority": "medium",
            "title": "Optimize Sleep Duration",
            "description": (
                f"At {sleep_hours:.1f} hrs, you're close to optimal. "
                f"National Sleep Foundation recommends 7-9 hours."
            ),
            "expected_impact": "Optimal sleep improves heart rate recovery and hormonal balance",
        })

    if glucose > 140:
        recs.append({
            "category": "nutrition",
            "priority": "high",
            "title": "Glucose Management Diet",
            "description": (
                f"Glucose at {glucose:.0f} mg/dL is in the impaired range. "
                f"Reduce refined carbohydrates, increase fiber intake (25-30g/day)."
            ),
            "expected_impact": "Dietary changes can reduce fasting glucose by 15-30 mg/dL in 4-8 weeks",
        })

    if calorie_intake > 2500 and bmi >= 25:
        recs.append({
            "category": "nutrition",
            "priority": "medium",
            "title": "Caloric Balance Adjustment",
            "description": (
                f"Intake of {calorie_intake:.0f} kcal with BMI {bmi:.1f} suggests caloric surplus. "
                f"A moderate 300-500 kcal deficit supports sustainable weight loss."
            ),
            "expected_impact": "5% body weight loss improves insulin sensitivity by ~20%",
        })

    if segment.get("segment") in ["High Risk", "Pre-Diabetic"]:
        recs.append({
            "category": "monitoring",
            "priority": "high",
            "title": "Regular Health Monitoring",
            "description": (
                f"As a {segment['segment']} patient, regular monitoring is essential. "
                f"Track fasting glucose weekly, blood pressure bi-weekly."
            ),
            "expected_impact": "Early detection enables 50%+ better outcomes in diabetes prevention",
        })

    if "diabetes" in conditions:
        recs.append({
            "category": "monitoring",
            "priority": "high",
            "title": "Diabetes Management Protocol",
            "description": (
                "Coordinate with your endocrinologist. Monitor post-meal glucose spikes. "
                "Ensure medication adherence and discuss exercise plans with your doctor."
            ),
            "expected_impact": "Structured management reduces complications by 40-60%",
        })

    if "hypertension" in conditions and hr > 85:
        recs.append({
            "category": "exercise",
            "priority": "high",
            "title": "Cardiovascular Risk Reduction",
            "description": (
                f"Heart rate at {hr:.0f} BPM with hypertension indicates elevated cardiovascular load. "
                f"Focus on low-impact aerobic exercise (swimming, cycling, walking)."
            ),
            "expected_impact": "Regular aerobic exercise reduces resting HR by 5-10 BPM in 4-8 weeks",
        })

    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: priority_order.get(r["priority"], 99))
    return recs


# ═══════════════════════════════════════════════════════════════════════════
# 4. EARLY WARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def check_early_warnings(
    vitals_history: list[dict],
    current_vitals: dict,
    patient_conditions: list[str] = None,
) -> list[dict]:
    """Analyze vitals trends to detect dangerous patterns."""
    warnings = []
    conditions = [c.lower() for c in (patient_conditions or [])]

    glucose = current_vitals.get("glucose", 100)
    hr = current_vitals.get("heart_rate", 75)
    sleep = current_vitals.get("sleep_hours", 7)
    steps = current_vitals.get("steps", 5000)

    # ── Immediate threshold alerts ──
    if glucose >= 250:
        warnings.append({
            "level": "critical",
            "title": "Dangerously High Glucose",
            "message": f"Glucose at {glucose:.0f} mg/dL is in the danger zone. This may indicate diabetic ketoacidosis risk.",
            "action": "Seek immediate medical attention. Check for ketones if diabetic.",
        })
    elif glucose >= 200:
        warnings.append({
            "level": "warning",
            "title": "Very High Glucose",
            "message": f"Glucose at {glucose:.0f} mg/dL exceeds the diabetic threshold (200 mg/dL).",
            "action": "Consult your healthcare provider within 24 hours.",
        })

    if hr >= 120:
        warnings.append({
            "level": "warning",
            "title": "Elevated Heart Rate",
            "message": f"Resting heart rate at {hr:.0f} BPM is significantly elevated.",
            "action": "Rest and hydrate. If persistent, seek medical evaluation.",
        })

    if sleep < 4:
        warnings.append({
            "level": "warning",
            "title": "Severe Sleep Deprivation",
            "message": f"Only {sleep:.1f} hours of sleep. Chronic sleep deprivation under 4 hours impairs cognitive function.",
            "action": "Prioritize sleep tonight. Consider sleep hygiene improvements.",
        })

    # ── Pre-diabetes trend detection ──
    if 100 <= glucose < 140:
        warnings.append({
            "level": "info",
            "title": "Pre-Diabetes Indicator",
            "message": f"Glucose at {glucose:.0f} mg/dL is in the pre-diabetic range (100-139 mg/dL). Early intervention is highly effective.",
            "action": "Increase physical activity and reduce refined carbohydrate intake.",
        })

    # ── Sedentary lifestyle detection ──
    if steps < 3000:
        warnings.append({
            "level": "warning",
            "title": "Sedentary Lifestyle Detected",
            "message": f"Only {steps:,} steps today. Prolonged inactivity increases cardiovascular and metabolic risk.",
            "action": "Take a 10-minute walk every hour. Set movement reminders.",
        })

    # ── Sleep deficiency pattern ──
    if 4 <= sleep < 6:
        warnings.append({
            "level": "info",
            "title": "Sleep Deficiency",
            "message": f"Sleep at {sleep:.1f} hours is below the 7-hour minimum. This impacts glucose regulation and recovery.",
            "action": "Establish a consistent bedtime. Limit screen time before sleep.",
        })

    # ── Trend analysis (if we have history) ──
    if len(vitals_history) >= 5:
        recent_glucose = [v.get("glucose", 100) for v in vitals_history[-5:]]
        recent_hr = [v.get("heart_rate", 75) for v in vitals_history[-5:]]

        glucose_trend = recent_glucose[-1] - recent_glucose[0]
        if glucose_trend > 30:
            warnings.append({
                "level": "warning",
                "title": "Rising Glucose Trend",
                "message": f"Glucose has risen by {glucose_trend:.0f} mg/dL over recent readings. This upward trend warrants attention.",
                "action": "Review recent meals and activity. Consider a glucose tolerance test.",
            })

        hr_trend = recent_hr[-1] - recent_hr[0]
        if hr_trend > 15:
            warnings.append({
                "level": "info",
                "title": "Increasing Heart Rate Trend",
                "message": f"Heart rate has increased by {hr_trend:.0f} BPM over recent readings.",
                "action": "Monitor for continued elevation. Ensure adequate hydration and rest.",
            })

    return warnings


# ═══════════════════════════════════════════════════════════════════════════
# 5. TREND INTELLIGENCE (NEW)
# ═══════════════════════════════════════════════════════════════════════════

def compute_trend_intelligence(
    baseline_vitals: dict,
    final_vitals: dict,
    simulation_days: int,
) -> list[dict]:
    """
    Compute trend intelligence insights like:
    "Your glucose has decreased 12% over 14 days"

    Returns list of trend insight objects.
    """
    trends = []

    for key, label, unit in [
        ("heart_rate", "Heart Rate", "BPM"),
        ("glucose", "Blood Glucose", "mg/dL"),
        ("steps", "Daily Steps", "steps"),
        ("sleep_hours", "Sleep Duration", "hrs"),
    ]:
        before = baseline_vitals.get(key, 0)
        after = final_vitals.get(key, 0)
        if before == 0:
            continue

        change = after - before
        pct = (change / abs(before)) * 100

        if abs(pct) < 1:
            direction = "stable"
            icon = "→"
        elif pct > 0:
            direction = "increased"
            icon = "↑"
        else:
            direction = "decreased"
            icon = "↓"

        # Determine if the change is positive or negative for health
        is_good = False
        if key == "heart_rate" and change < 0:
            is_good = True
        elif key == "glucose" and change < 0:
            is_good = True
        elif key == "steps" and change > 0:
            is_good = True
        elif key == "sleep_hours" and change > 0 and after <= 9:
            is_good = True

        trends.append({
            "vital": key,
            "label": label,
            "unit": unit,
            "before": round(before, 1) if isinstance(before, float) else before,
            "after": round(after, 1) if isinstance(after, float) else after,
            "change": round(change, 1),
            "percent_change": round(pct, 1),
            "direction": direction,
            "icon": icon,
            "is_positive": is_good if direction != "stable" else None,
            "insight": f"{label} {direction} {abs(pct):.1f}% over {simulation_days} days ({before:.0f} → {after:.0f} {unit})",
        })

    return trends


# ═══════════════════════════════════════════════════════════════════════════
# 6. INTERVENTION IMPACT SCORE (NEW)
# ═══════════════════════════════════════════════════════════════════════════

def compute_intervention_impact(
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    risk_before: float,
    risk_after: float,
) -> list[dict]:
    """
    Estimate how much each intervention contributed to risk change.
    Example: "Exercise contributed 65% to your improvement"

    Uses a weighted attribution model based on lifestyle medicine evidence.
    """
    total_change = risk_before - risk_after  # positive = improvement

    if abs(total_change) < 0.5:
        return [{
            "intervention": "No Change",
            "contribution_percent": 0,
            "detail": "Risk score remained stable — no significant intervention impact",
        }]

    # Evidence-based contribution weights
    # Exercise: strongest modifiable factor for metabolic health
    exercise_weight = min(1.0, exercise_minutes / 45) * 0.45
    # Sleep: second most impactful
    sleep_weight = min(1.0, max(0, sleep_hours - 5) / 4) * 0.30
    # Nutrition: caloric moderation
    calorie_weight = min(1.0, max(0, 2500 - calorie_intake) / 1000) * 0.25

    total_weight = exercise_weight + sleep_weight + calorie_weight
    if total_weight == 0:
        total_weight = 1

    impacts = []

    exercise_pct = round((exercise_weight / total_weight) * 100, 0)
    sleep_pct = round((sleep_weight / total_weight) * 100, 0)
    nutrition_pct = round(100 - exercise_pct - sleep_pct, 0)

    impacts.append({
        "intervention": "Exercise",
        "icon": "🏃",
        "contribution_percent": int(exercise_pct),
        "detail": f"{exercise_minutes:.0f} min/day of exercise",
        "is_primary": exercise_pct >= sleep_pct and exercise_pct >= nutrition_pct,
    })
    impacts.append({
        "intervention": "Sleep",
        "icon": "🌙",
        "contribution_percent": int(sleep_pct),
        "detail": f"{sleep_hours:.1f} hours of nightly sleep",
        "is_primary": sleep_pct > exercise_pct and sleep_pct > nutrition_pct,
    })
    impacts.append({
        "intervention": "Nutrition",
        "icon": "🍽️",
        "contribution_percent": int(nutrition_pct),
        "detail": f"{calorie_intake:.0f} kcal daily intake",
        "is_primary": nutrition_pct > exercise_pct and nutrition_pct > sleep_pct,
    })

    # Sort by contribution
    impacts.sort(key=lambda x: -x["contribution_percent"])

    return impacts


# ═══════════════════════════════════════════════════════════════════════════
# 7. STABILITY INDICATOR (NEW)
# ═══════════════════════════════════════════════════════════════════════════

def compute_stability_indicator(
    future_vitals: list[dict],
) -> dict:
    """
    Analyze the projected vitals timeline for stability.
    Returns: { status: "Stable"|"Moderate"|"Volatile", details: {...} }
    """
    if not future_vitals or len(future_vitals) < 3:
        return {"status": "Insufficient Data", "detail": {}}

    detail = {}
    for key in ["heart_rate", "glucose", "steps", "sleep_hours"]:
        values = [v.get(key, 0) for v in future_vitals]
        if not values:
            continue
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            detail[key] = {"cv_percent": 0, "stability": "stable"}
            continue
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        cv = (std / abs(mean_val)) * 100

        if cv < 3:
            stability = "stable"
        elif cv < 8:
            stability = "moderate"
        else:
            stability = "volatile"

        detail[key] = {
            "mean": round(mean_val, 1),
            "std": round(std, 2),
            "cv_percent": round(cv, 2),
            "stability": stability,
        }

    # Overall status
    statuses = [d.get("stability", "stable") for d in detail.values()]
    if "volatile" in statuses:
        overall = "Volatile"
    elif "moderate" in statuses:
        overall = "Moderate"
    else:
        overall = "Stable"

    return {
        "status": overall,
        "detail": detail,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 8. GROQ-POWERED STRUCTURED RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

async def generate_groq_recommendations(
    health_score: dict,
    segment: dict,
    risk_before: float,
    risk_after: float,
    baseline_vitals: dict,
    final_vitals: dict,
    patient_age: int,
    bmi: float,
    conditions: list[str],
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    simulation_days: int,
) -> dict | None:
    """
    Generate a structured personalized health action plan via Groq AI.

    Returns a JSON dict with:
      { summary, key_factors, risk_level, confidence, recommendations }

    Falls back to a structured template if Groq fails.
    """
    # ── Build structured fallback first (guaranteed) ──
    fallback = _build_action_plan_fallback(
        health_score, segment, risk_before, risk_after,
        baseline_vitals, final_vitals, patient_age, bmi,
        conditions, exercise_minutes, sleep_hours, calorie_intake,
        simulation_days,
    )

    if not GROQ_API_KEY:
        return fallback

    prompt = (
        f"You are a clinical digital twin health advisor. Generate a personalized, "
        f"actionable health plan for this patient.\n\n"
        f"PATIENT: {patient_age}-year-old, BMI {bmi:.1f}, "
        f"conditions: {', '.join(conditions) if conditions else 'none'}.\n"
        f"SEGMENT: {segment.get('segment', 'Unknown')}\n"
        f"HEALTH SCORE: {health_score.get('health_score', 'N/A')}/100 (Grade {health_score.get('grade', '?')})\n"
        f"WEAKEST AREA: {health_score.get('weakest_area', 'unknown')}\n\n"
        f"CURRENT VITALS: HR {baseline_vitals.get('heart_rate')} BPM, "
        f"Glucose {baseline_vitals.get('glucose')} mg/dL, "
        f"Steps {baseline_vitals.get('steps')}, Sleep {baseline_vitals.get('sleep_hours')} hrs\n\n"
        f"AFTER {simulation_days}-DAY SIMULATION (exercise {exercise_minutes} min, "
        f"sleep {sleep_hours} hrs, {calorie_intake} kcal): "
        f"Risk went from {risk_before:.1f} to {risk_after:.1f}.\n\n"
        f"Respond with a JSON object containing: summary, key_factors, risk_level, confidence, recommendations."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a certified health advisor for a digital twin patient simulation. "
                    "You MUST respond ONLY with a valid JSON object. No markdown, no code fences, no extra text. "
                    "JSON keys: \"summary\" (string, 2-3 sentences), \"key_factors\" (array of 3-4 strings), "
                    "\"risk_level\" (\"Low\"/\"Medium\"/\"High\"), \"confidence\" (string like \"85%\"), "
                    "\"recommendations\" (array of 3-5 specific actionable strings). "
                    "Never diagnose. Use 'may help', 'consider', 'discuss with your doctor'. "
                    "Include specific numbers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"].strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Validate structure
            required_keys = {"summary", "key_factors", "risk_level", "confidence", "recommendations"}
            if required_keys.issubset(set(parsed.keys())):
                return parsed
            else:
                print(f"⚠️  Groq action plan missing keys — using fallback")
                return fallback
    except json.JSONDecodeError:
        print(f"⚠️  Groq returned non-JSON — using structured fallback")
        return fallback
    except Exception as e:
        print(f"⚠️  Groq recommendations error: {e}")
        return fallback


def _build_action_plan_fallback(
    health_score, segment, risk_before, risk_after,
    baseline_vitals, final_vitals, patient_age, bmi,
    conditions, exercise_minutes, sleep_hours, calorie_intake,
    simulation_days,
) -> dict:
    """Build a structured action plan fallback (no AI needed)."""
    risk_change = risk_before - risk_after
    conditions_lower = [c.lower() for c in (conditions or [])]

    if risk_change > 15:
        summary = (
            f"Excellent projected improvement. Your risk score is expected to drop by "
            f"{risk_change:.1f} points over {simulation_days} days. "
            f"The combination of exercise and lifestyle changes shows strong positive impact."
        )
        risk_level = "Low"
        confidence = "87%"
    elif risk_change > 5:
        summary = (
            f"Moderate improvement projected. Risk drops from {risk_before:.1f} to {risk_after:.1f} "
            f"over {simulation_days} days. Increasing exercise intensity could accelerate results."
        )
        risk_level = "Medium"
        confidence = "79%"
    elif risk_change > 0:
        summary = (
            f"Slight improvement expected. Risk moves from {risk_before:.1f} to {risk_after:.1f}. "
            f"Consider more aggressive lifestyle modifications for meaningful change."
        )
        risk_level = "Medium"
        confidence = "72%"
    else:
        summary = (
            f"Current parameters may not sufficiently reduce risk. "
            f"Score projected at {risk_after:.1f}/100. Review exercise and sleep targets."
        )
        risk_level = "High"
        confidence = "68%"

    key_factors = []
    glucose = baseline_vitals.get("glucose", 100)
    if glucose > 120:
        key_factors.append(f"Glucose at {glucose:.0f} mg/dL needs attention")
    if exercise_minutes < 30:
        key_factors.append(f"Exercise at {exercise_minutes:.0f} min/day is below recommended")
    if sleep_hours < 7:
        key_factors.append(f"Sleep target of {sleep_hours:.1f} hrs is suboptimal")
    if bmi >= 25:
        key_factors.append(f"BMI {bmi:.1f} indicates excess weight")
    if not key_factors:
        key_factors.append("Vitals are within acceptable ranges")

    recommendations = []
    if exercise_minutes < 45:
        recommendations.append(f"Increase exercise to 45+ min/day (currently {exercise_minutes:.0f} min)")
    if sleep_hours < 7.5:
        recommendations.append(f"Aim for 7.5+ hours of sleep (currently {sleep_hours:.1f} hrs)")
    if calorie_intake > 2200:
        recommendations.append(f"Reduce caloric intake to ~2,000 kcal (currently {calorie_intake:.0f})")
    if glucose > 120:
        recommendations.append("Add fiber-rich foods and reduce refined carbohydrates")
    recommendations.append("Schedule a follow-up health assessment in 2 weeks")

    return {
        "summary": summary,
        "key_factors": key_factors[:4],
        "risk_level": risk_level,
        "confidence": confidence,
        "recommendations": recommendations[:5],
    }
