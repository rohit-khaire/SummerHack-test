"""
health_engine.py — Clinical decision support engine.

Provides:
    • compute_health_score()      — Composite 0-100 wellness metric
    • classify_patient_segment()  — Risk stratification (Low / Pre-Diabetic / High / Critical)
    • generate_recommendations()  — Personalized action plans
    • check_early_warnings()      — Real-time alert generation
    • generate_groq_recommendations() — AI-powered personalized plan via Groq
"""

import math
import os
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

    Unlike risk_score (where high = bad), health_score represents
    overall wellness.  Based on AHA & WHO guidelines for optimal ranges.

    Returns:
        {
            "health_score": float,
            "grade": "A" | "B" | "C" | "D" | "F",
            "component_scores": { ... },
            "weakest_area": str,
            "strongest_area": str,
        }
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
    elif glucose <= 125:  # pre-diabetic range
        metabolic = 100 - (glucose - 100) * 2.0
    elif glucose <= 180:
        metabolic = 50 - (glucose - 125) * 0.6
    else:
        metabolic = max(0, 17 - (glucose - 180) * 0.5)

    # Activity: WHO recommends 150+ min/week moderate exercise (~22 min/day)
    # and 7000+ steps/day
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
        sleep_score = 85  # slightly suboptimal
    else:
        sleep_score = max(0, 55 - (5 - sleep_hours) * 20)

    # Body composition: optimal BMI 18.5-24.9 (WHO)
    if 18.5 <= bmi <= 24.9:
        body = 100
    elif 25 <= bmi < 30:
        body = 100 - (bmi - 25) * 6
    elif bmi >= 30:
        body = max(0, 70 - (bmi - 30) * 4)
    else:  # underweight
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

    # Age adjustment: slight penalty for age-related decline
    age_penalty = max(0, (age - 40) * 0.15)
    health_score = max(0, min(100, health_score - age_penalty))

    # Grade
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

    # Find strongest and weakest areas
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
    """
    Classify the patient into a clinical risk segment based on
    ADA (American Diabetes Association) and AHA guidelines.

    Returns:
        {
            "segment": str,
            "segment_description": str,
            "segment_color": str,
            "risk_factors": list[str],
            "monitoring_frequency": str,
        }
    """
    conditions = [c.lower() for c in (conditions or [])]
    risk_factors = []

    # ── Identify risk factors ──
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

    # ── Classify segment ──
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
    """
    Generate personalized, actionable health recommendations.

    Each recommendation includes:
        - category: exercise | nutrition | sleep | monitoring
        - priority: high | medium | low
        - title: short heading
        - description: detailed advice
        - expected_impact: what improvement to expect
    """
    recs = []
    conditions = [c.lower() for c in (conditions or [])]
    glucose = baseline_vitals.get("glucose", 100)
    hr = baseline_vitals.get("heart_rate", 75)
    steps = baseline_vitals.get("steps", 5000)

    # ── Exercise recommendations ──
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
                f"2-3 times per week to improve glucose uptake by skeletal muscle. "
                f"Consider interval training for cardiovascular benefit."
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
                f"Aim for 7,000-10,000 steps. Take walking meetings, use stairs, "
                f"set hourly movement reminders."
            ),
            "expected_impact": "Each additional 2,000 steps/day reduces cardiovascular risk by ~8%",
        })

    # ── Sleep recommendations ──
    if sleep_hours < 6:
        recs.append({
            "category": "sleep",
            "priority": "high",
            "title": "Address Sleep Deprivation",
            "description": (
                f"Sleeping {sleep_hours:.1f} hrs is critically low. Sleep deprivation impairs "
                f"glucose regulation, elevates cortisol, and increases appetite hormones. "
                f"Establish a consistent bedtime, limit screens 1hr before sleep, keep room cool and dark."
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
                f"National Sleep Foundation recommends 7-9 hours. "
                f"Focus on sleep quality: consistent schedule, reduced caffeine after 2 PM."
            ),
            "expected_impact": "Optimal sleep improves heart rate recovery and hormonal balance",
        })

    # ── Nutrition recommendations ──
    if glucose > 140:
        recs.append({
            "category": "nutrition",
            "priority": "high",
            "title": "Glucose Management Diet",
            "description": (
                f"Glucose at {glucose:.0f} mg/dL is in the impaired range. "
                f"Reduce refined carbohydrates, increase fiber intake (25-30g/day), "
                f"focus on whole grains, legumes, and non-starchy vegetables. "
                f"Consider meal timing — avoid large meals before sleep."
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
                f"A moderate 300-500 kcal deficit (not extreme restriction) supports sustainable "
                f"weight loss of 0.5-1 lb/week while preserving muscle mass."
            ),
            "expected_impact": "5% body weight loss improves insulin sensitivity by ~20%",
        })

    # ── Monitoring recommendations ──
    if segment.get("segment") in ["High Risk", "Pre-Diabetic"]:
        recs.append({
            "category": "monitoring",
            "priority": "high",
            "title": "Regular Health Monitoring",
            "description": (
                f"As a {segment['segment']} patient, regular monitoring is essential. "
                f"Track fasting glucose weekly, blood pressure bi-weekly. "
                f"Consider an HbA1c test every 3 months for long-term glucose tracking. "
                f"Consult a healthcare provider for a comprehensive metabolic panel."
            ),
            "expected_impact": "Early detection enables 50%+ better outcomes in diabetes prevention",
        })

    # ── Condition-specific recommendations ──
    if "diabetes" in conditions:
        recs.append({
            "category": "monitoring",
            "priority": "high",
            "title": "Diabetes Management Protocol",
            "description": (
                "With a diabetes diagnosis, coordinate with your endocrinologist. "
                "Monitor post-meal glucose spikes 2 hours after eating. "
                "Ensure medication adherence and discuss exercise plans with your doctor "
                "as physical activity directly affects insulin requirements."
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
                f"Focus on low-impact aerobic exercise (swimming, cycling, walking). "
                f"DASH diet (rich in fruits, vegetables, low-fat dairy) can reduce blood pressure."
            ),
            "expected_impact": "Regular aerobic exercise reduces resting HR by 5-10 BPM in 4-8 weeks",
        })

    # Sort by priority
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
    """
    Analyze vitals trends to detect dangerous patterns.

    Returns list of warnings with:
        - level: "info" | "warning" | "critical"
        - title: short description
        - message: detailed explanation
        - action: recommended immediate action
    """
    warnings = []
    conditions = [c.lower() for c in (patient_conditions or [])]

    glucose = current_vitals.get("glucose", 100)
    hr = current_vitals.get("heart_rate", 75)
    sleep = current_vitals.get("sleep_hours", 7)

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
            "message": f"Only {sleep:.1f} hours of sleep. Chronic sleep deprivation under 4 hours impairs cognitive function and metabolic health.",
            "action": "Prioritize sleep tonight. Consider sleep hygiene improvements.",
        })

    # ── Trend analysis (if we have history) ──
    if len(vitals_history) >= 5:
        recent_glucose = [v.get("glucose", 100) for v in vitals_history[-5:]]
        recent_hr = [v.get("heart_rate", 75) for v in vitals_history[-5:]]

        # Rising glucose trend
        glucose_trend = recent_glucose[-1] - recent_glucose[0]
        if glucose_trend > 30:
            warnings.append({
                "level": "warning",
                "title": "Rising Glucose Trend",
                "message": f"Glucose has risen by {glucose_trend:.0f} mg/dL over recent readings. This upward trend warrants attention.",
                "action": "Review recent meals and activity. Consider a glucose tolerance test.",
            })

        # Rising HR trend
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
# 5. GROQ-POWERED PERSONALIZED RECOMMENDATIONS
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
) -> str | None:
    """Generate a personalized health action plan via Groq AI."""
    if not GROQ_API_KEY:
        return None

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
        f"Generate a concise 3-point action plan with specific daily targets. "
        f"Focus on the weakest area. Include expected timeline for improvement. "
        f"Use encouraging but honest tone. Do NOT format as markdown. "
        f"End with a one-line motivational statement."
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
                    "Provide specific, actionable, evidence-based recommendations. "
                    "Never diagnose. Use phrases like 'may help', 'consider', 'discuss with your doctor'. "
                    "Keep response under 200 words. No markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 350,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️  Groq recommendations error: {e}")
        return None
