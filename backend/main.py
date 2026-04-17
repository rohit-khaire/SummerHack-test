"""
main.py — FastAPI application for the Digital Twin Patient system.

Features:
    • Background task that generates vitals every 2 s and stores them
    • REST endpoints for vitals, prediction, and what-if simulation
    • Advanced simulation with health score, segmentation, recommendations
    • WebSocket endpoint that pushes live vitals to connected dashboards
    • Early warning system for dangerous trends
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import connect_db, close_db, insert_vitals, get_latest_vitals, get_vitals_history
from simulator import generate_vitals, apply_simulation, simulate_advanced
from model import predict_risk, assess_risk_advanced
from patient import PatientProfile, compute_modifiers
from groq_explain import generate_explanations
from health_engine import (
    compute_health_score,
    classify_patient_segment,
    generate_recommendations,
    check_early_warnings,
    generate_groq_recommendations,
)

# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Keeps track of active WebSocket clients."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        payload = json.dumps(data, default=str)
        for ws in list(self.active):
            try:
                await ws.send_text(payload)
            except Exception:
                if ws in self.active:
                    self.active.remove(ws)


manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Background vitals generator
# ---------------------------------------------------------------------------

async def vitals_loop():
    """Generate vitals every 2 seconds, store in DB, and broadcast via WS."""
    while True:
        vitals = generate_vitals()
        await insert_vitals(vitals)

        risk = predict_risk(
            vitals["heart_rate"],
            vitals["glucose"],
            vitals["steps"],
            vitals["sleep_hours"],
        )

        # Compute mini health score for live dashboard
        hs = compute_health_score(
            vitals["heart_rate"], vitals["glucose"],
            vitals["steps"], vitals["sleep_hours"],
        )

        broadcast_data = {
            **vitals,
            "risk_score": risk,
            "health_score": hs["health_score"],
            "health_grade": hs["grade"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await manager.broadcast(broadcast_data)
        await asyncio.sleep(2)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    task = asyncio.create_task(vitals_loop())
    print("🚀 Vitals background loop started")
    yield
    task.cancel()
    await close_db()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Digital Twin — Patient Decision Support System",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class SimulationRequest(BaseModel):
    exercise_increase: bool = False
    better_sleep: bool = False


class PatientInput(BaseModel):
    age: int = Field(default=35, ge=18, le=90)
    weight_kg: float = Field(default=75.0, ge=30, le=250)
    height_cm: float = Field(default=170.0, ge=100, le=230)
    conditions: list[str] = Field(default=[])


class AdvancedSimulationRequest(BaseModel):
    patient: PatientInput = Field(default_factory=PatientInput)
    exercise_minutes: float = Field(default=30.0, ge=0, le=120)
    sleep_hours: float = Field(default=7.0, ge=3, le=12)
    calorie_intake: float = Field(default=2200.0, ge=800, le=5000)
    simulation_days: int = Field(default=14, ge=1, le=90)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/vitals")
async def latest_vitals():
    vitals = await get_latest_vitals()
    if not vitals:
        return {"message": "No vitals recorded yet"}
    return vitals


@app.get("/vitals/history")
async def vitals_history():
    history = await get_vitals_history(30)
    return history


@app.get("/predict")
async def predict():
    vitals = await get_latest_vitals()
    if not vitals:
        return {"risk_score": 0, "message": "No vitals yet"}
    score = predict_risk(
        vitals["heart_rate"], vitals["glucose"],
        vitals["steps"], vitals["sleep_hours"],
    )
    return {"risk_score": score}


@app.post("/simulate")
async def simulate(req: SimulationRequest):
    """Legacy simulation — kept for backward compatibility."""
    vitals = await get_latest_vitals()
    if not vitals:
        return {"message": "No vitals yet"}

    current_risk = predict_risk(
        vitals["heart_rate"], vitals["glucose"],
        vitals["steps"], vitals["sleep_hours"],
    )
    adjusted = apply_simulation(vitals, req.exercise_increase, req.better_sleep)
    adjusted_risk = predict_risk(
        adjusted["heart_rate"], adjusted["glucose"],
        adjusted["steps"], adjusted["sleep_hours"],
    )

    return {
        "original_vitals": {k: vitals[k] for k in ["heart_rate", "glucose", "steps", "sleep_hours"]},
        "adjusted_vitals": adjusted,
        "current_risk": current_risk,
        "simulated_risk": adjusted_risk,
        "risk_change": round(adjusted_risk - current_risk, 1),
    }


@app.post("/simulate-advanced")
async def simulate_advanced_endpoint(req: AdvancedSimulationRequest):
    """
    Advanced physiological simulation with full clinical decision support.

    Returns: time-series projection, risk assessment, health score,
    patient segmentation, personalized recommendations, early warnings,
    explainability, and optional Groq AI action plan.
    """
    vitals = await get_latest_vitals()
    if not vitals:
        return {"message": "No vitals yet — wait for the simulation loop to generate data"}

    baseline = {
        "heart_rate": vitals["heart_rate"],
        "glucose": vitals["glucose"],
        "steps": vitals["steps"],
        "sleep_hours": vitals["sleep_hours"],
    }

    # Build patient profile
    profile = PatientProfile(
        age=req.patient.age,
        weight_kg=req.patient.weight_kg,
        height_cm=req.patient.height_cm,
        conditions=req.patient.conditions,
    )

    # ── Time-series simulation ──
    timeline = simulate_advanced(
        baseline_vitals=baseline,
        profile=profile,
        exercise_minutes=req.exercise_minutes,
        sleep_hours=req.sleep_hours,
        calorie_intake=req.calorie_intake,
        simulation_days=req.simulation_days,
    )
    final_day = timeline[-1] if timeline else baseline

    # ── Risk assessment: before & after ──
    risk_before = assess_risk_advanced(
        heart_rate=baseline["heart_rate"],
        glucose=baseline["glucose"],
        steps=baseline["steps"],
        sleep_hours=baseline["sleep_hours"],
        age=profile.age,
        bmi=profile.bmi,
        exercise_minutes=0,
        calorie_intake=req.calorie_intake,
    )

    risk_after = assess_risk_advanced(
        heart_rate=final_day["heart_rate"],
        glucose=final_day["glucose"],
        steps=final_day["steps"],
        sleep_hours=final_day["sleep_hours"],
        age=profile.age,
        bmi=profile.bmi,
        exercise_minutes=req.exercise_minutes,
        calorie_intake=req.calorie_intake,
    )

    improvement_pct = 0.0
    if risk_before["risk_score"] > 0:
        improvement_pct = round(
            (risk_before["risk_score"] - risk_after["risk_score"]) / risk_before["risk_score"] * 100, 1
        )

    # ── Health Score (before & after) ──
    health_before = compute_health_score(
        baseline["heart_rate"], baseline["glucose"],
        baseline["steps"], baseline["sleep_hours"],
        age=profile.age, bmi=profile.bmi, exercise_minutes=0,
    )
    health_after = compute_health_score(
        final_day["heart_rate"], final_day["glucose"],
        final_day["steps"], final_day["sleep_hours"],
        age=profile.age, bmi=profile.bmi,
        exercise_minutes=req.exercise_minutes,
    )

    # ── Patient Segmentation ──
    segment = classify_patient_segment(
        glucose=baseline["glucose"],
        bmi=profile.bmi,
        age=profile.age,
        heart_rate=baseline["heart_rate"],
        risk_score=risk_before["risk_score"],
        conditions=profile.conditions,
    )

    # ── Recommendations ──
    recommendations = generate_recommendations(
        health_score=health_before,
        segment=segment,
        baseline_vitals=baseline,
        exercise_minutes=req.exercise_minutes,
        sleep_hours=req.sleep_hours,
        calorie_intake=req.calorie_intake,
        age=profile.age,
        bmi=profile.bmi,
        conditions=profile.conditions,
    )

    # ── Early Warnings ──
    history = await get_vitals_history(10)
    warnings = check_early_warnings(
        vitals_history=history,
        current_vitals=baseline,
        patient_conditions=profile.conditions,
    )

    # ── Explanations (rule-based + Groq) ──
    explain_result = await generate_explanations(
        baseline=baseline,
        final_vitals=final_day,
        exercise_minutes=req.exercise_minutes,
        sleep_hours=req.sleep_hours,
        calorie_intake=req.calorie_intake,
        risk_before=risk_before["risk_score"],
        risk_after=risk_after["risk_score"],
        patient_age=profile.age,
        conditions=profile.conditions,
        feature_contributions=risk_after.get("feature_contributions"),
    )

    # ── Groq AI Action Plan (in parallel with above) ──
    ai_action_plan = await generate_groq_recommendations(
        health_score=health_after,
        segment=segment,
        risk_before=risk_before["risk_score"],
        risk_after=risk_after["risk_score"],
        baseline_vitals=baseline,
        final_vitals=final_day,
        patient_age=profile.age,
        bmi=profile.bmi,
        conditions=profile.conditions,
        exercise_minutes=req.exercise_minutes,
        sleep_hours=req.sleep_hours,
        calorie_intake=req.calorie_intake,
        simulation_days=req.simulation_days,
    )

    # ── Profile metadata ──
    mods = compute_modifiers(profile)

    # ── Model metadata ──
    import os, joblib
    meta_path = os.path.join(os.path.dirname(__file__), "model_metadata.pkl")
    model_meta = {}
    if os.path.exists(meta_path):
        model_meta = joblib.load(meta_path)

    # Combine all anomalies, deduplicate
    all_anomalies = risk_after.get("anomalies", []) + risk_before.get("anomalies", [])
    seen = set()
    unique_anomalies = []
    for a in all_anomalies:
        if a["message"] not in seen:
            seen.add(a["message"])
            unique_anomalies.append(a)

    return {
        # Patient
        "patient_profile": {
            "age": profile.age,
            "bmi": profile.bmi,
            "bmi_category": mods["bmi_category"],
            "conditions": profile.conditions,
            "adaptation_rate": mods["adaptation_rate"],
        },

        # Vitals
        "baseline_vitals": baseline,
        "future_vitals": timeline,

        # Risk
        "risk_before": risk_before,
        "risk_after": risk_after,
        "improvement_percent": improvement_pct,

        # Health Score (NEW)
        "health_score_before": health_before,
        "health_score_after": health_after,

        # Patient Segment (NEW)
        "patient_segment": segment,

        # Recommendations (NEW)
        "recommendations": recommendations,

        # Early Warnings (NEW)
        "early_warnings": warnings,

        # Explainability
        "explanation": explain_result["explanations"],
        "ai_summary": explain_result.get("ai_summary"),
        "ai_action_plan": ai_action_plan,

        # Anomalies
        "anomalies": unique_anomalies,

        # Model trust metadata (NEW)
        "model_info": {
            "dataset": f"{model_meta.get('pima_samples', 0)} PIMA + {model_meta.get('synthetic_samples', 0)} synthetic",
            "accuracy_r2": model_meta.get("r2", "N/A"),
            "accuracy_mae": model_meta.get("mae", "N/A"),
            "features_used": model_meta.get("features", []),
        },

        # Disclaimer (NEW)
        "disclaimer": (
            "This system is a simulation tool for educational and research purposes only. "
            "It does not provide medical diagnoses. Always consult a qualified healthcare "
            "professional for medical advice, diagnosis, or treatment decisions."
        ),
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/vitals")
async def websocket_vitals(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
