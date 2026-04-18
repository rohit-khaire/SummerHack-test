"""
simulator.py — Physiological simulation engine with stable vital generation.

Key improvements over v2:
    • StableVitalGenerator: EMA-smoothed vitals with state memory (no random jumps)
    • Demo spike/dip system: manual control via API for demonstration
    • Gaussian noise: small σ values for each vital (realistic micro-variation)
    • Gradual drift: vitals drift slowly around a patient baseline
    • Time-consistent: every reading depends on the previous state

Models lifestyle interventions as coupled exponential-decay processes
approaching new equilibria.

Key equations:
    EMA:  V_new = α * V_prev + (1 - α) * V_target
    Decay: V(t) = V_target + (V_0 - V_target) × exp(-t / τ)

References:
    • GLUT4-mediated glucose uptake (Richter & Hargreaves, Physiol Rev 2013)
    • Resting HR adaptation (Reimers et al., Prev Med 2018)
    • Sleep-glucose link (Spiegel et al., Lancet 1999)
"""

import math
import random
from collections import deque
from patient import PatientProfile, compute_modifiers


# ---------------------------------------------------------------------------
# Stable Vital Generator (CORE — replaces old generate_vitals)
# ---------------------------------------------------------------------------

class StableVitalGenerator:
    """
    Generates realistic, time-consistent vitals using EMA smoothing.

    Each reading depends on the previous state. No random jumps.
    Small Gaussian noise produces micro-variation. Manual spike/dip
    triggers are available for demonstration purposes.
    """

    # Physiological baseline (healthy adult defaults)
    BASELINE = {
        "heart_rate": 75.0,
        "glucose": 105.0,
        "steps": 5500,
        "sleep_hours": 7.0,
    }

    # Noise σ for each vital (small, realistic)
    NOISE_SIGMA = {
        "heart_rate": 1.5,    # ±1.5 BPM typical resting variation
        "glucose": 2.0,       # ±2 mg/dL between readings
        "steps": 150,         # ±150 steps (accumulated counter varies)
        "sleep_hours": 0.15,  # ±0.15 hrs
    }

    # Physiological clamp ranges
    CLAMP = {
        "heart_rate": (50, 150),
        "glucose": (60, 300),
        "steps": (0, 20000),
        "sleep_hours": (3.0, 10.0),
    }

    # Slow drift targets (the vitals wander around these over minutes)
    DRIFT_SPEED = 0.005  # how fast the drift target changes per tick

    def __init__(self):
        self.state = dict(self.BASELINE)
        self.history: deque[dict] = deque(maxlen=10)
        self.alpha = 0.7  # EMA smoothing: 70% previous + 30% new
        self._tick = 0

        # Drift targets — slowly wander to create natural variation
        self._drift_target = dict(self.BASELINE)
        self._drift_direction = {k: random.choice([-1, 1]) for k in self.BASELINE}

        # Spike/dip system — controlled by API
        self._spike_active: dict[str, dict] = {}  # key -> {magnitude, remaining_ticks, direction}

    # ── Public API ──

    def generate(self) -> dict:
        """Generate next vitals reading (EMA-smoothed, time-consistent)."""
        self._tick += 1

        # 1. Update drift targets (slow wander — changes direction every ~40 ticks)
        self._update_drift()

        # 2. Compute raw target (drift + Gaussian noise)
        raw = {}
        for key in self.BASELINE:
            noise = random.gauss(0, self.NOISE_SIGMA[key])
            raw[key] = self._drift_target[key] + noise

        # 3. Apply active spikes/dips
        for key, spike in list(self._spike_active.items()):
            if spike["remaining"] > 0:
                # Spike decays linearly over its duration
                decay = spike["remaining"] / spike["total_ticks"]
                raw[key] += spike["magnitude"] * decay * spike["direction"]
                spike["remaining"] -= 1
            else:
                del self._spike_active[key]

        # 4. EMA smoothing: new = α * previous + (1-α) * raw
        smoothed = {}
        for key in self.BASELINE:
            prev = self.state[key]
            smoothed[key] = self.alpha * prev + (1 - self.alpha) * raw[key]

        # 5. Clamp to physiological ranges
        for key in self.BASELINE:
            lo, hi = self.CLAMP[key]
            smoothed[key] = max(lo, min(hi, smoothed[key]))

        # 6. Round and type-cast
        result = {
            "heart_rate": round(smoothed["heart_rate"], 1),
            "glucose": round(smoothed["glucose"], 1),
            "steps": int(round(smoothed["steps"])),
            "sleep_hours": round(smoothed["sleep_hours"], 1),
        }

        # 7. Update state and history
        self.state = {k: smoothed[k] for k in self.BASELINE}
        self.history.append(dict(result))

        return result

    def trigger_spike(self, direction: str = "up") -> dict:
        """
        Trigger a clinically plausible spike (up) or dip (down) for demo.
        The spike decays back to baseline over 8-12 ticks.

        Args:
            direction: "up" for spike, "down" for dip

        Returns:
            Dict describing what was triggered.
        """
        dir_mult = 1 if direction == "up" else -1
        duration = random.randint(8, 12)

        # Clinically plausible magnitudes (large enough to cross classification thresholds
        # even with EMA smoothing α=0.7)
        spikes = {
            "heart_rate": {"magnitude": 40.0, "desc": "stress/anxiety response"},
            "glucose": {"magnitude": 90.0, "desc": "post-meal glucose surge" if dir_mult > 0 else "insulin response"},
            "steps": {"magnitude": 3000.0, "desc": "sudden activity burst" if dir_mult > 0 else "rest period"},
            "sleep_hours": {"magnitude": 2.0, "desc": "oversleep" if dir_mult > 0 else "insomnia episode"},
        }

        triggered = []
        for key, info in spikes.items():
            self._spike_active[key] = {
                "magnitude": info["magnitude"],
                "direction": dir_mult,
                "total_ticks": duration,
                "remaining": duration,
            }
            triggered.append({
                "vital": key,
                "direction": direction,
                "magnitude": info["magnitude"] * dir_mult,
                "reason": info["desc"],
                "decay_ticks": duration,
            })

        return {
            "triggered": triggered,
            "message": f"Demo {'spike' if direction == 'up' else 'dip'} triggered — will decay over {duration} readings",
        }

    def get_recent_history(self) -> list[dict]:
        """Return last 10 readings for trend analysis."""
        return list(self.history)

    def get_stability_metrics(self) -> dict:
        """
        Compute stability metrics from recent history.
        Returns coefficient of variation and stability classification.
        """
        if len(self.history) < 3:
            return {"status": "initializing", "detail": {}}

        detail = {}
        for key in ["heart_rate", "glucose", "steps", "sleep_hours"]:
            values = [h[key] for h in self.history]
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                cv = 0
            else:
                variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                std = variance ** 0.5
                cv = (std / abs(mean_val)) * 100  # coefficient of variation %
            detail[key] = {
                "mean": round(mean_val, 1),
                "std": round(std if mean_val != 0 else 0, 2),
                "cv_percent": round(cv, 2),
            }

        # Overall stability: if all CVs < 5%, stable; < 10% moderate; else volatile
        avg_cv = sum(d["cv_percent"] for d in detail.values()) / len(detail)
        if avg_cv < 3:
            status = "stable"
        elif avg_cv < 7:
            status = "moderate"
        else:
            status = "volatile"

        return {
            "status": status,
            "avg_cv_percent": round(avg_cv, 2),
            "detail": detail,
        }

    def get_trend_analysis(self) -> dict:
        """
        Analyze trends from recent history.
        Returns percentage change and direction for each vital.
        """
        if len(self.history) < 5:
            return {"available": False, "message": "Need at least 5 readings for trend analysis"}

        trends = {}
        history_list = list(self.history)
        for key in ["heart_rate", "glucose", "steps", "sleep_hours"]:
            old_avg = sum(h[key] for h in history_list[:3]) / 3
            new_avg = sum(h[key] for h in history_list[-3:]) / 3
            if old_avg == 0:
                pct_change = 0
            else:
                pct_change = ((new_avg - old_avg) / abs(old_avg)) * 100

            if abs(pct_change) < 1:
                direction = "stable"
            elif pct_change > 0:
                direction = "increasing"
            else:
                direction = "decreasing"

            trends[key] = {
                "direction": direction,
                "percent_change": round(pct_change, 1),
                "from_avg": round(old_avg, 1),
                "to_avg": round(new_avg, 1),
            }

        return {"available": True, "trends": trends}

    # ── Internal ──

    def _update_drift(self):
        """Slowly wander drift targets for natural variation."""
        drift_ranges = {
            "heart_rate": (65, 90),
            "glucose": (85, 135),
            "steps": (3000, 8000),
            "sleep_hours": (5.5, 8.0),
        }
        for key in self.BASELINE:
            lo, hi = drift_ranges[key]
            step = self.DRIFT_SPEED * (hi - lo) * self._drift_direction[key]
            self._drift_target[key] += step

            # Reverse direction at boundaries
            if self._drift_target[key] >= hi:
                self._drift_target[key] = hi
                self._drift_direction[key] = -1
            elif self._drift_target[key] <= lo:
                self._drift_target[key] = lo
                self._drift_direction[key] = 1

            # Small random direction changes (5% chance per tick)
            if random.random() < 0.05:
                self._drift_direction[key] *= -1


# ---------------------------------------------------------------------------
# Global generator instance (used by main.py vitals loop)
# ---------------------------------------------------------------------------
vital_generator = StableVitalGenerator()


# ---------------------------------------------------------------------------
# Backward-compatible wrappers
# ---------------------------------------------------------------------------

def generate_vitals() -> dict:
    """Produce a single reading using the stable generator."""
    return vital_generator.generate()


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
# Advanced physiological simulation (for /simulate-advanced)
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

    Uses EMA smoothing for day-to-day transitions (no random jumps).
    """
    mods = compute_modifiers(profile)

    # ── Extract baselines ──
    hr_0 = baseline_vitals.get("heart_rate", 85.0)
    gl_0 = baseline_vitals.get("glucose", 130.0)
    steps_0 = baseline_vitals.get("steps", 3000)
    sleep_0 = baseline_vitals.get("sleep_hours", 6.0)

    # ── Compute target equilibria under intervention ──

    # 1) GLUCOSE TARGET
    exercise_effect = _sigmoid(exercise_minutes, midpoint=30, steepness=0.08)
    glucose_reduction_pct = 0.18 * exercise_effect
    calorie_excess = max(0, calorie_intake - 2000) / 500.0
    calorie_penalty_pct = 0.03 * calorie_excess
    sleep_deficit = max(0, 7.0 - sleep_hours)
    sleep_glucose_penalty_pct = 0.05 * sleep_deficit
    glucose_target = gl_0 * (1.0 - glucose_reduction_pct + calorie_penalty_pct + sleep_glucose_penalty_pct)
    glucose_target = max(mods["glucose_floor"], glucose_target)

    # 2) HEART RATE TARGET
    hr_exercise_effect = _sigmoid(exercise_minutes, midpoint=30, steepness=0.06)
    hr_reduction_pct = 0.12 * hr_exercise_effect
    sleep_benefit = max(0, sleep_hours - 6.0)
    hr_sleep_reduction_pct = 0.02 * min(sleep_benefit, 3.0)
    hr_target = hr_0 * (1.0 - hr_reduction_pct - hr_sleep_reduction_pct)
    hr_target = max(mods["hr_floor"], hr_target)

    # 3) STEPS TARGET
    steps_from_exercise = int(exercise_minutes * 150)
    steps_target = min(15000, steps_0 + steps_from_exercise)

    # 4) SLEEP TARGET
    sleep_target = min(9.0, sleep_hours)

    # ── Time constants (days) — scaled by patient profile ──
    tau_glucose = 5.0 * mods["age_factor"]
    tau_hr = 7.0 * mods["age_factor"]
    tau_steps = 2.0
    tau_sleep = 4.0 * mods["age_factor"]

    # ── Day-by-day simulation with smoothing ──
    timeline = []
    prev_hr = hr_0
    prev_gl = gl_0
    prev_steps = float(steps_0)
    prev_sleep = sleep_0
    ema_alpha = 0.6  # day-to-day smoothing for simulation

    for day in range(1, simulation_days + 1):
        # Exponential decay toward target
        hr_t = hr_target + (hr_0 - hr_target) * math.exp(-day / tau_hr)
        gl_t = glucose_target + (gl_0 - glucose_target) * math.exp(-day / tau_glucose)
        steps_t = steps_target + (steps_0 - steps_target) * math.exp(-day / tau_steps)
        sleep_t = sleep_target + (sleep_0 - sleep_target) * math.exp(-day / tau_sleep)

        # Add small daily noise (much smaller than before — ±1% not ±2%)
        noise_scale = 0.01
        hr_t *= (1 + random.gauss(0, noise_scale))
        gl_t *= (1 + random.gauss(0, noise_scale))
        steps_t *= (1 + random.gauss(0, noise_scale * 1.5))
        sleep_t *= (1 + random.gauss(0, noise_scale * 0.5))

        # EMA smooth against previous day (prevents day-to-day jumps)
        hr_t = ema_alpha * prev_hr + (1 - ema_alpha) * hr_t
        gl_t = ema_alpha * prev_gl + (1 - ema_alpha) * gl_t
        steps_t = ema_alpha * prev_steps + (1 - ema_alpha) * steps_t
        sleep_t = ema_alpha * prev_sleep + (1 - ema_alpha) * sleep_t

        # Clamp to physiological ranges
        hr_t = max(50, min(150, hr_t))
        gl_t = max(60, min(300, gl_t))
        steps_t = max(0, min(20000, steps_t))
        sleep_t = max(3.0, min(10.0, sleep_t))

        # Non-linear interaction: high glucose + low activity → HR spike
        if gl_t > 160 and steps_t < 3000:
            hr_t += 3.0 * (gl_t - 160) / 100.0

        # Update previous values for next iteration's EMA
        prev_hr = hr_t
        prev_gl = gl_t
        prev_steps = steps_t
        prev_sleep = sleep_t

        timeline.append({
            "day": day,
            "heart_rate": round(hr_t, 1),
            "glucose": round(gl_t, 1),
            "steps": int(round(steps_t)),
            "sleep_hours": round(sleep_t, 1),
        })

    return timeline
