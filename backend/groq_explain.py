"""
groq_explain.py — AI-powered health explanations via Groq API
with STRUCTURED JSON output and intelligent rule-based fallback.

All AI responses are returned as structured JSON objects, never raw text.
If Groq fails or returns non-JSON, a structured fallback template is used.
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
# 1. Structured fallback template (guaranteed format)
# ---------------------------------------------------------------------------

def _generate_structured_fallback(
    baseline: dict,
    final_vitals: dict,
    exercise_minutes: float,
    sleep_hours: float,
    calorie_intake: float,
    risk_before: float,
    risk_after: float,
    patient_age: int,
    conditions: list[str],
) -> dict:
    """
    Produce a structured health analysis using deterministic rules.
    Guaranteed JSON format — never fails.
    """
    conditions_lower = [c.lower().strip() for c in conditions]
    key_factors = []
    recommendations = []

    # ── Identify key factors ──
    glucose_val = baseline.get("glucose", 100)
    hr_val = baseline.get("heart_rate", 75)
    steps_val = baseline.get("steps", 5000)
    sleep_val = baseline.get("sleep_hours", 7)

    if glucose_val > 140:
        key_factors.append(f"Elevated glucose ({glucose_val:.0f} mg/dL — above 140 threshold)")
    elif glucose_val > 100:
        key_factors.append(f"Borderline glucose ({glucose_val:.0f} mg/dL — pre-diabetic range)")

    if hr_val > 90:
        key_factors.append(f"Elevated resting heart rate ({hr_val:.0f} BPM)")

    if steps_val < 5000:
        key_factors.append(f"Low physical activity ({steps_val:,} steps — below 5,000 target)")

    if sleep_val < 6:
        key_factors.append(f"Insufficient sleep ({sleep_val:.1f} hrs — below 7hr minimum)")

    if "diabetes" in conditions_lower:
        key_factors.append("Pre-existing diabetes diagnosis")
    if "hypertension" in conditions_lower:
        key_factors.append("Pre-existing hypertension diagnosis")

    if not key_factors:
        key_factors.append("All vitals within normal ranges")

    # ── Risk level mapping ──
    risk_change = risk_after - risk_before
    if risk_after >= 70:
        risk_level = "High"
    elif risk_after >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # ── Confidence ──
    confidence = "78%"  # fallback default
    if abs(risk_change) > 15:
        confidence = "85%"
    elif abs(risk_change) < 3:
        confidence = "72%"

    # ── Summary ──
    if risk_change < -10:
        summary = (f"Your health risk is projected to decrease significantly "
                   f"from {risk_before:.1f} to {risk_after:.1f}. "
                   f"The intervention shows strong positive impact.")
    elif risk_change < -3:
        summary = (f"Your health risk shows a modest improvement "
                   f"from {risk_before:.1f} to {risk_after:.1f}. "
                   f"Continued adherence will yield greater benefits.")
    elif risk_change > 3:
        summary = (f"Your health risk is projected to increase slightly "
                   f"from {risk_before:.1f} to {risk_after:.1f}. "
                   f"Consider adjusting exercise and sleep targets.")
    else:
        summary = (f"Your health risk remains stable at approximately "
                   f"{risk_after:.1f}/100. Current parameters maintain your baseline.")

    # ── Recommendations ──
    if exercise_minutes < 30:
        recommendations.append(
            f"Increase daily exercise to at least 30 minutes — "
            f"currently at {exercise_minutes:.0f} min"
        )
    if sleep_hours < 7:
        recommendations.append(
            f"Improve sleep duration to 7+ hours — "
            f"currently targeting {sleep_hours:.1f} hrs"
        )
    if glucose_val > 120:
        recommendations.append(
            "Reduce refined carbohydrates and increase fiber intake to 25-30g/day"
        )
    if steps_val < 7000:
        recommendations.append(
            f"Aim for 7,000+ daily steps — currently at {steps_val:,}"
        )
    if calorie_intake > 2500:
        recommendations.append(
            f"Consider reducing caloric intake from {calorie_intake:.0f} to ~2,000 kcal"
        )
    if patient_age >= 45:
        recommendations.append(
            "Schedule regular metabolic panel checkups (HbA1c every 3 months)"
        )

    if not recommendations:
        recommendations.append("Maintain current healthy lifestyle patterns")

    return {
        "summary": summary,
        "key_factors": key_factors[:5],
        "risk_level": risk_level,
        "confidence": confidence,
        "recommendations": recommendations[:5],
    }


# ---------------------------------------------------------------------------
# 2. Rule-based explanations (detailed physiological insights)
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
    conditions_lower = [c.lower().strip() for c in conditions]

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
# 3. Groq API call (structured JSON output)
# ---------------------------------------------------------------------------

async def _call_groq_structured(prompt: str) -> dict | None:
    """
    Call Groq API and return a STRUCTURED JSON response.
    If the API returns non-JSON, returns None (fallback will be used).
    """
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
                    "You MUST respond ONLY with a valid JSON object, nothing else. No markdown, no code fences. "
                    "The JSON must have exactly these keys:\n"
                    '  "summary": string (2-3 sentences, specific health insight with numbers),\n'
                    '  "key_factors": array of 2-4 strings (specific factors affecting health),\n'
                    '  "risk_level": "Low" or "Medium" or "High",\n'
                    '  "confidence": string like "82%",\n'
                    '  "recommendations": array of 3-5 strings (specific actionable advice)\n'
                    "\n"
                    "Rules: Do NOT give medical diagnoses. Use 'projected to' and 'may help'. "
                    "Include specific numbers from the data. Keep each string under 100 characters."
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

            # Try to parse as JSON
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Validate required keys
            required_keys = {"summary", "key_factors", "risk_level", "confidence", "recommendations"}
            if not required_keys.issubset(set(parsed.keys())):
                print(f"⚠️  Groq response missing keys: {required_keys - set(parsed.keys())}")
                return None

            return parsed
    except json.JSONDecodeError:
        print(f"⚠️  Groq returned non-JSON response — using fallback")
        return None
    except Exception as e:
        print(f"⚠️  Groq API error: {e}")
        return None


# ---------------------------------------------------------------------------
# 4. Public API — generate explanations (structured)
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
            "explanations": [...],           # rule-based insights (always present)
            "ai_summary": { ... } | null,    # structured JSON from Groq (or fallback)
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

    # Generate structured fallback (always ready)
    structured_fallback = _generate_structured_fallback(
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

    # Attempt Groq AI structured response
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
            f"Respond with a JSON object analyzing this patient's health trajectory."
        )
        ai_summary = await _call_groq_structured(prompt)

    # Use fallback if Groq failed or returned None
    if ai_summary is None:
        ai_summary = structured_fallback

    return {
        "explanations": explanations,
        "ai_summary": ai_summary,
    }
