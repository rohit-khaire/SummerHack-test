"""
groq_explain.py — AI-powered health explanations via Groq API,
with an intelligent rule-based fallback when the API is unavailable.
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ---------------------------------------------------------------------------
# 1. Rule-based fallback explanations
# ---------------------------------------------------------------------------

def _generate_template_explanations(
    baseline: dict,
    final_vitals: dict,
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    risk_before: float,
    risk_after: float,
    patient_age: int,
    conditions: list[str],
) -> list[str]:
    """
    Produce medically meaningful explanations using deterministic rules.
    Each explanation references specific numbers and physiological mechanisms.
    """
    explanations = []

    # ── Exercise effects ──
    if exercise_minutes >= 15:
        gl_drop = baseline.get("glucose", 130) - final_vitals.get("glucose", 130)
        if gl_drop > 0:
            explanations.append(
                f"Exercising {exercise_minutes:.0f} min/day activates GLUT4 glucose transporters "
                f"in skeletal muscle, improving insulin sensitivity. Your glucose is projected to "
                f"drop by ~{gl_drop:.0f} mg/dL over the simulation period."
            )
        hr_drop = baseline.get("heart_rate", 85) - final_vitals.get("heart_rate", 85)
        if hr_drop > 2:
            explanations.append(
                f"Sustained aerobic exercise increases stroke volume, allowing the heart to pump "
                f"more blood per beat. Resting heart rate is projected to decrease by ~{hr_drop:.0f} BPM."
            )

    # ── Sleep effects ──
    if sleep_hours >= 7:
        if baseline.get("sleep_hours", 6) < 7:
            explanations.append(
                f"Increasing sleep to {sleep_hours:.1f} hours restores parasympathetic nervous system "
                f"activity, reducing sympathetic overdrive. This lowers resting heart rate and "
                f"improves overnight glucose regulation."
            )
    elif sleep_hours < 6:
        explanations.append(
            f"Sleep of only {sleep_hours:.1f} hours is below the recommended 7–9 hours. "
            f"Sleep deprivation impairs glucose tolerance and elevates cortisol, "
            f"increasing cardiovascular risk."
        )

    # ── Calorie effects ──
    if calorie_intake > 2500:
        explanations.append(
            f"A caloric intake of {calorie_intake:.0f} kcal/day exceeds typical maintenance needs. "
            f"Excess calories contribute to insulin resistance and weight gain over time."
        )
    elif calorie_intake < 1500:
        explanations.append(
            f"A caloric intake of {calorie_intake:.0f} kcal/day is quite restrictive. "
            f"While this may support weight loss, ensure adequate nutrition to avoid metabolic slowdown."
        )

    # ── Condition-specific notes ──
    conditions_lower = [c.lower().strip() for c in conditions]
    if "diabetes" in conditions_lower:
        explanations.append(
            f"As a diabetic patient, glucose improvements may be slower due to chronic insulin "
            f"resistance. Consistent exercise over 30+ min/day shows the greatest benefit."
        )
    if "hypertension" in conditions_lower:
        explanations.append(
            f"With hypertension, the elevated baseline heart rate reflects increased vascular "
            f"resistance. Regular aerobic exercise is the most effective non-pharmacological "
            f"intervention for lowering blood pressure."
        )

    # ── Age-specific notes ──
    if patient_age >= 60:
        explanations.append(
            f"At age {patient_age}, physiological adaptations occur more gradually. "
            f"Improvements in glucose control and heart rate may take 2–3× longer "
            f"compared to younger patients."
        )

    # ── Overall risk summary ──
    risk_change = risk_after - risk_before
    if risk_change < -10:
        explanations.append(
            f"Overall health risk is projected to decrease from {risk_before:.1f} to "
            f"{risk_after:.1f} — a significant {abs(risk_change):.1f}-point improvement. "
            f"Sustaining these lifestyle changes is key to long-term benefit."
        )
    elif risk_change < -3:
        explanations.append(
            f"Risk score decreases from {risk_before:.1f} to {risk_after:.1f} — a modest "
            f"but meaningful improvement. Consider increasing exercise duration for greater impact."
        )
    elif risk_change > 3:
        explanations.append(
            f"⚠️ Risk score is projected to increase from {risk_before:.1f} to {risk_after:.1f}. "
            f"This may be driven by insufficient exercise or sleep. Review your targets."
        )

    return explanations if explanations else [
        "No significant changes detected based on the current intervention parameters."
    ]


# ---------------------------------------------------------------------------
# 2. Groq API call
# ---------------------------------------------------------------------------

async def _call_groq(prompt: str) -> str | None:
    """Call Groq API and return the response text, or None on failure."""
    if not GROQ_API_KEY:
        return None

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
                    "You are a clinical health AI assistant for a Digital Twin patient simulation system. "
                    "Provide concise, medically accurate, empathetic health insights. "
                    "Use specific numbers from the data provided. "
                    "Do NOT give medical diagnoses. Use phrases like 'projected to' and 'may help'. "
                    "Keep your response to 3-5 sentences. Do not use markdown formatting."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️  Groq API error: {e}")
        return None


# ---------------------------------------------------------------------------
# 3. Public API — generate explanations
# ---------------------------------------------------------------------------

async def generate_explanations(
    baseline: dict,
    final_vitals: dict,
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    risk_before: float,
    risk_after: float,
    patient_age: int = 35,
    conditions: list[str] | None = None,
    feature_contributions: dict | None = None,
) -> dict:
    """
    Generate explanations for a simulation result.

    Returns:
        {
            "explanations": [...],       # rule-based insights
            "ai_summary": "..." | null,  # Groq-generated paragraph (or null)
        }
    """
    conditions = conditions or []

    # Always generate rule-based explanations (fast, reliable)
    explanations = _generate_template_explanations(
        baseline=baseline,
        final_vitals=final_vitals,
        exercise_minutes=exercise_minutes,
        sleep_hours=sleep_hours,
        calorie_intake=calorie_intake,
        risk_before=risk_before,
        risk_after=risk_after,
        patient_age=patient_age,
        conditions=conditions,
    )

    # Attempt Groq AI summary as a bonus
    ai_summary = None
    if GROQ_API_KEY:
        prompt = (
            f"A {patient_age}-year-old patient "
            f"{'with ' + ', '.join(conditions) if conditions else 'with no pre-existing conditions'} "
            f"ran a health simulation.\n\n"
            f"BASELINE VITALS: HR {baseline.get('heart_rate', 'N/A')} BPM, "
            f"Glucose {baseline.get('glucose', 'N/A')} mg/dL, "
            f"Steps {baseline.get('steps', 'N/A')}, "
            f"Sleep {baseline.get('sleep_hours', 'N/A')} hrs.\n\n"
            f"INTERVENTION: Exercise {exercise_minutes} min/day, "
            f"Sleep target {sleep_hours} hrs, "
            f"Calorie intake {calorie_intake} kcal/day.\n\n"
            f"PROJECTED END VITALS: HR {final_vitals.get('heart_rate', 'N/A')} BPM, "
            f"Glucose {final_vitals.get('glucose', 'N/A')} mg/dL, "
            f"Steps {final_vitals.get('steps', 'N/A')}, "
            f"Sleep {final_vitals.get('sleep_hours', 'N/A')} hrs.\n\n"
            f"RISK: Changed from {risk_before:.1f} to {risk_after:.1f} (out of 100).\n\n"
            f"Provide a brief, personalized health insight for this patient."
        )
        ai_summary = await _call_groq(prompt)

    return {
        "explanations": explanations,
        "ai_summary": ai_summary,
    }
