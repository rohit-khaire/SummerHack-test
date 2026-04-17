"""
simulator.py — Physiological simulation engine.

Models lifestyle interventions as coupled exponential-decay processes
approaching new equilibria.  Each vital sign moves toward a target value
determined by the intervention parameters and patient profile, at a rate
governed by the patient's adaptation speed.

Key equations (grounded in exercise-physiology literature):
    V(t) = V_target + (V_0 - V_target) × exp(-t / τ)

Where:
    V_0      = current (baseline) vital value
    V_target = new equilibrium under the intervention
    τ        = time constant (days), scaled by age & profile
    t        = simulation day

References (simplified for MVP):
    • GLUT4-mediated glucose uptake improves ~18% with moderate exercise
      (Richter & Hargreaves, Physiol Rev 2013)
    • Resting HR drops ~7-12% with sustained aerobic training
      (Reimers et al., Prev Med 2018)
    • Sleep deprivation raises HR ~5-10 BPM and impairs glucose tolerance
      (Spiegel et al., Lancet 1999)
"""

import math
import random
from patient import PatientProfile, compute_modifiers


# ---------------------------------------------------------------------------
# Kept for backward compatibility with the live-vitals background loop
# ---------------------------------------------------------------------------

def generate_vitals() -> dict:
    """Produce a single reading of patient vitals with realistic random values."""
    return {
        "heart_rate": round(random.uniform(60, 120), 1),
        "glucose": round(random.uniform(80, 180), 1),
        "steps": random.randint(0, 10000),
        "sleep_hours": round(random.uniform(4, 9), 1),
    }


def apply_simulation(vitals: dict, exercise_increase: bool, better_sleep: bool) -> dict:
    """Legacy simulation — kept for /simulate backward compatibility."""
    adjusted = vitals.copy()
    if exercise_increase:
        adjusted["glucose"] = round(adjusted["glucose"] * 0.85, 1)
        adjusted["steps"] = min(10000, int(adjusted["steps"] * 1.30))
    if better_sleep:
        adjusted["heart_rate"] = round(adjusted["heart_rate"] * 0.90, 1)
        adjusted["sleep_hours"] = min(9.0, round(adjusted["sleep_hours"] * 1.20, 1))
    return adjusted


# ---------------------------------------------------------------------------
# Sigmoid utility
# ---------------------------------------------------------------------------

def _sigmoid(x: float, midpoint: float = 0.0, steepness: float = 1.0) -> float:
    """Logistic sigmoid function mapped to [0, 1]."""
    z = steepness * (x - midpoint)
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, z))))


# ---------------------------------------------------------------------------
# Advanced physiological simulation
# ---------------------------------------------------------------------------

def simulate_advanced(
    baseline_vitals: dict,
    profile: PatientProfile,
    exercise_minutes: float = 0.0,
    sleep_hours: float = 7.0,
    calorie_intake: float = 2200.0,
    simulation_days: int = 14,
) -> list[dict]:
    """
    Run a time-series physiological simulation.

    Models how each vital sign evolves day-by-day when the patient adopts
    new lifestyle parameters, given their individual profile.

    Args:
        baseline_vitals:  Current vitals (heart_rate, glucose, steps, sleep_hours).
        profile:          PatientProfile with age, weight, height, conditions.
        exercise_minutes: Daily exercise target (minutes).
        sleep_hours:      Nightly sleep target (hours).
        calorie_intake:   Daily calorie intake (kcal).
        simulation_days:  How many days to project (1–90).

    Returns:
        List of dicts, one per day, with keys:
            day, heart_rate, glucose, steps, sleep_hours
    """
    mods = compute_modifiers(profile)

    # ── Extract baselines ──
    hr_0 = baseline_vitals.get("heart_rate", 85.0)
    gl_0 = baseline_vitals.get("glucose", 130.0)
    steps_0 = baseline_vitals.get("steps", 3000)
    sleep_0 = baseline_vitals.get("sleep_hours", 6.0)

    # ── Compute target equilibria under intervention ──

    # 1) GLUCOSE TARGET
    #    Exercise effect: GLUT4 translocation improves insulin sensitivity.
    #    Modeled as a sigmoid of exercise_minutes with midpoint at 30 min.
    #    Maximum reduction: ~18% for a healthy patient.
    exercise_effect = _sigmoid(exercise_minutes, midpoint=30, steepness=0.08)
    glucose_reduction_pct = 0.18 * exercise_effect

    #    Calorie effect: excess calories impair glucose control.
    #    Baseline 2000 kcal = neutral; each +500 kcal → +3% glucose.
    calorie_excess = max(0, calorie_intake - 2000) / 500.0
    calorie_penalty_pct = 0.03 * calorie_excess

    #    Sleep effect: poor sleep impairs glucose tolerance (~5% per hour deficit).
    sleep_deficit = max(0, 7.0 - sleep_hours)
    sleep_glucose_penalty_pct = 0.05 * sleep_deficit

    glucose_target = gl_0 * (1.0 - glucose_reduction_pct + calorie_penalty_pct + sleep_glucose_penalty_pct)
    glucose_target = max(mods["glucose_floor"], glucose_target)

    # 2) HEART RATE TARGET
    #    Aerobic training effect: sustained exercise lowers resting HR.
    #    ~12% reduction at 60+ minutes/day (sigmoid saturates).
    hr_exercise_effect = _sigmoid(exercise_minutes, midpoint=30, steepness=0.06)
    hr_reduction_pct = 0.12 * hr_exercise_effect

    #    Sleep effect: adequate sleep enhances parasympathetic tone.
    #    Each hour above 6 → ~2% HR reduction, up to ~8% at 9 hrs.
    sleep_benefit = max(0, sleep_hours - 6.0)
    hr_sleep_reduction_pct = 0.02 * min(sleep_benefit, 3.0)

    hr_target = hr_0 * (1.0 - hr_reduction_pct - hr_sleep_reduction_pct)
    hr_target = max(mods["hr_floor"], hr_target)

    # 3) STEPS TARGET
    #    Steps scale linearly with exercise_minutes.
    #    ~150 steps per minute of exercise (mix of walking/running).
    steps_from_exercise = int(exercise_minutes * 150)
    steps_target = min(15000, steps_0 + steps_from_exercise)

    # 4) SLEEP TARGET
    #    Sleep improves gradually as the patient establishes a routine.
    #    Target is the sleep_hours parameter; body adapts.
    sleep_target = min(9.0, sleep_hours)

    # ── Time constants (days) — scaled by patient profile ──
    tau_glucose = 5.0 * mods["age_factor"]   # glucose adapts in ~5 days (young)
    tau_hr = 7.0 * mods["age_factor"]        # HR adapts in ~7 days baseline
    tau_steps = 2.0                           # steps ramp up quickly
    tau_sleep = 4.0 * mods["age_factor"]     # sleep routine in ~4 days

    # ── Day-by-day simulation ──
    timeline = []
    for day in range(1, simulation_days + 1):
        # Exponential decay toward target
        hr_t = hr_target + (hr_0 - hr_target) * math.exp(-day / tau_hr)
        gl_t = glucose_target + (gl_0 - glucose_target) * math.exp(-day / tau_glucose)
        steps_t = steps_target + (steps_0 - steps_target) * math.exp(-day / tau_steps)
        sleep_t = sleep_target + (sleep_0 - sleep_target) * math.exp(-day / tau_sleep)

        # Add small daily noise for realism (±2% of current value)
        noise_scale = 0.02
        hr_t *= (1 + random.gauss(0, noise_scale))
        gl_t *= (1 + random.gauss(0, noise_scale))
        steps_t *= (1 + random.gauss(0, noise_scale * 1.5))
        sleep_t *= (1 + random.gauss(0, noise_scale * 0.5))

        # Clamp to physiological ranges
        hr_t = max(50, min(150, hr_t))
        gl_t = max(60, min(300, gl_t))
        steps_t = max(0, min(20000, int(steps_t)))
        sleep_t = max(3.0, min(10.0, sleep_t))

        # Non-linear interaction: high glucose + low activity → HR spike
        if gl_t > 160 and steps_t < 3000:
            hr_t += 3.0 * (gl_t - 160) / 100.0  # mild tachycardia from metabolic stress

        timeline.append({
            "day": day,
            "heart_rate": round(hr_t, 1),
            "glucose": round(gl_t, 1),
            "steps": steps_t,
            "sleep_hours": round(sleep_t, 1),
        })

    return timeline
