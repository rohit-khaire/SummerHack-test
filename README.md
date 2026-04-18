# 🫀 Digital Twin — Patient Clinical Decision Support System

> **An AI-powered health decision platform** that creates a virtual replica of a patient, predicts future health risks using ML trained on real clinical data (PIMA Diabetes), and generates personalized, explainable recommendations.

---

## 🎤 Demo Story (The Problem We Solve)

### Meet Priya, 45, Pre-Diabetic

Priya is a 45-year-old software engineer with a BMI of 28.3. Her doctor told her she's "pre-diabetic" — her fasting glucose is 135 mg/dL. She was given generic advice: "eat better, exercise more."

**The problem?** Priya doesn't know:
- *How much* exercise makes a real difference?
- Will her glucose improve in 7 days or 30?
- Is she closer to diabetes or to recovery?
- What should she prioritize — sleep, exercise, or diet?

**Current solutions fail because:**
- Fitness apps track *activity*, not *metabolic risk*
- Doctor visits happen every 3 months — too late for early intervention
- Generic advice doesn't account for *her* body, *her* conditions
- No tool shows *before vs after* impact of lifestyle changes

### How Digital Twin Solves This

Priya opens the Digital Twin dashboard. She enters her profile (age 45, weight 82kg, diabetic). The system immediately:

1. **Classifies her** as "Pre-Diabetic" with 3 risk factors
2. **Scores her health** at 52/100 (Grade C) — weakness: metabolic
3. **Shows her risk** at 48.2/100 (Moderate)

She adjusts the sliders: 45 min exercise, 8 hrs sleep, 2000 kcal diet, 14-day simulation.

**The simulation shows:**
- Glucose drops from 135 → 118 mg/dL (gradual, exponential curve)
- Heart rate drops from 88 → 79 BPM
- Risk decreases by 38% (48.2 → 29.8)
- Health score improves to 71/100 (Grade B)

**The AI explains** *why*: "Exercise activates GLUT4 glucose transporters in your skeletal muscle, improving insulin sensitivity. Your glucose is projected to drop by ~17 mg/dL."

**The system recommends** specific actions: increase to 45 min/day walking, prioritize 7+ hours of sleep, reduce refined carbs.

**This is not a fitness app. This is a clinical decision support tool.**

---

## 🎯 Who Is This For?

| User | Use Case |
|------|----------|
| **Pre-diabetic patients** | Understand their metabolic risk trajectory |
| **Fitness-conscious users** | See exactly how lifestyle changes impact health markers |
| **Primary care doctors** | Quick patient risk stratification and intervention planning |
| **Health coaches** | Data-driven, personalized lifestyle recommendations |
| **Insurance companies** | Risk assessment and wellness program optimization |

---

## 🧬 Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────────┐   │
│  │Live Vitals│ │Health +  │ │ Clinical Simulation    │   │
│  │Cards     │ │Risk Bars │ │  • Patient Profile     │   │
│  └──────────┘ └──────────┘ │  • Lifestyle Sliders   │   │
│  ┌──────────┐              │  • Time-series Charts  │   │
│  │Real-time │              │  • Risk Comparison     │   │
│  │Trend     │              │  • Recommendations     │   │
│  │Chart     │              │  • AI Health Advisor   │   │
│  └──────────┘              └────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │ WebSocket + REST
┌───────────────────────┴─────────────────────────────────┐
│                   FastAPI Backend                         │
│  ┌────────────────┐  ┌──────────────────────────────┐   │
│  │Physiology Engine│  │ Health Engine                │   │
│  │• Exponential   │  │ • Health Score (AHA/WHO)     │   │
│  │  decay dynamics│  │ • Patient Segmentation (ADA) │   │
│  │• Non-linear    │  │ • Recommendation Engine      │   │
│  │  interactions  │  │ • Early Warning System       │   │
│  └────────────────┘  └──────────────────────────────┘   │
│  ┌────────────────┐  ┌──────────────────────────────┐   │
│  │ML Risk Model   │  │ Explainability Engine        │   │
│  │• PIMA-trained  │  │ • Feature contributions      │   │
│  │  RandomForest  │  │ • Rule-based explanations    │   │
│  │• IsolationForest│ │ • Groq AI health summaries   │   │
│  │  anomaly detect│  │ • Groq AI action plans       │   │
│  └────────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python 3.13) |
| ML | Scikit-learn — VotingRegressor ensemble for risk, GradientBoostingClassifier for disease classification, IsolationForest for anomaly detection |
| Training Data | **PIMA Indians Diabetes Dataset** (768 records) + 4000 synthetic, with ADA-inspired disease labels (Normal / Pre-Diabetic / Diabetic / High Cardiovascular Risk) |
| AI Explanations | Groq API (LLaMA 3.3 70B) + rule-based fallback |
| Database | MongoDB (Motor) / In-memory fallback |
| Real-time | WebSockets (2s interval) |
| Frontend | React 18 + Tailwind CSS 3 + Recharts |
| Bundler | Vite 5 |

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# (Optional) Add Groq API key for AI-powered recommendations
# Edit backend/.env → GROQ_API_KEY=gsk_your_key_here

# Train models (downloads PIMA dataset automatically)
python train_model.py

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npx vite --host
```

### 3. Open Dashboard

Navigate to **http://localhost:5173**

---

## API — POST /simulate-advanced

### Request
```json
{
  "patient": {
    "age": 45,
    "weight_kg": 82,
    "height_cm": 175,
    "conditions": ["diabetes"]
  },
  "exercise_minutes": 45,
  "sleep_hours": 7.5,
  "calorie_intake": 2000,
  "simulation_days": 14
}
```

### Response (key fields)
```json
{
  "patient_profile": { "age": 45, "bmi": 26.8, "bmi_category": "overweight" },

  "health_score_before": { "health_score": 52.3, "grade": "C", "weakest_area": "metabolic" },
  "health_score_after":  { "health_score": 71.4, "grade": "B", "weakest_area": "body_composition" },

  "patient_segment": {
    "segment": "Pre-Diabetic",
    "risk_factors": ["Pre-diabetic glucose", "Overweight (BMI 26.8)", "Age ≥45"],
    "monitoring_frequency": "Bi-weekly vitals check"
  },

  "risk_before": { "risk_score": 48.2, "risk_level": "Moderate", "confidence": 0.87 },
  "risk_after":  { "risk_score": 29.8, "risk_level": "Low", "confidence": 0.91 },
  "improvement_percent": 38.2,

  "future_vitals": [
    { "day": 1, "glucose": 134.2, "heart_rate": 87.1, ... },
    { "day": 7, "glucose": 125.3, ... },
    { "day": 14, "glucose": 118.4, ... }
  ],

  "recommendations": [
    {
      "category": "exercise",
      "priority": "high",
      "title": "Increase Daily Movement",
      "description": "...",
      "expected_impact": "5-15% glucose reduction within 2 weeks"
    }
  ],

  "early_warnings": [...],
  "explanation": ["Exercising 45 min/day activates GLUT4 glucose transporters..."],
  "ai_summary": "Based on your profile as a 45-year-old overweight patient...",
  "ai_action_plan": "1. Walk 45 minutes daily...",

  "model_info": {
    "dataset": "752 PIMA + 4000 synthetic",
    "accuracy_r2": 0.92,
    "accuracy_mae": 3.28
  },

  "disclaimer": "This system is a simulation tool for educational and research purposes only..."
}
```

---

## Model Validation

| Metric | Value |
|--------|-------|
| Training dataset | 752 PIMA (real) + 4000 synthetic = 4752 |
| R² Score | 0.92 |
| MAE | 3.28 |
| Top feature | Glucose (53.8% importance) |
| Anomaly detector | IsolationForest (5% contamination) |

### Why This Is Credible

1. **PIMA dataset** — Clinically validated, published in medical literature, used in 1000+ research papers
2. **Feature engineering** — Not just raw inputs; derived BMI, activity scores, glucose trends
3. **Non-linear interactions** — Glucose × inactivity interaction term models real metabolic synergy
4. **Confidence intervals** — Tree-variance based; the model knows when it's uncertain
5. **Anomaly detection** — Statistical outlier detection prevents garbage-in-garbage-out

---

## Clinical Grounding

| Feature | Clinical Basis |
|---------|---------------|
| Health Score weights | AHA cardiovascular guidelines, WHO activity recommendations |
| Glucose thresholds | ADA (American Diabetes Association) — pre-diabetic ≥100, diabetic ≥200 |
| Sleep recommendations | National Sleep Foundation — optimal 7-9 hours |
| BMI categories | WHO classification — overweight ≥25, obese ≥30 |
| Exercise effects | GLUT4 translocation (Richter & Hargreaves, Physiol Rev 2013) |
| HR adaptation | Aerobic training meta-analysis (Reimers et al., Prev Med 2018) |
| Sleep-glucose link | Sleep deprivation study (Spiegel et al., Lancet 1999) |

---

## Project Structure

```
DummyWatch/
├── backend/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── model.py             # ML risk assessment + anomaly detection
│   ├── simulator.py         # Physiological simulation engine
│   ├── patient.py           # Patient profile + modifiers
│   ├── health_engine.py     # Health score, segmentation, recommendations
│   ├── groq_explain.py      # AI explanations + action plans
│   ├── database.py          # MongoDB / in-memory storage
│   ├── train_model.py       # PIMA-grounded model training
│   ├── model.pkl            # Trained risk model
│   ├── anomaly_model.pkl    # Anomaly detector
│   ├── model_metadata.pkl   # Training metrics
│   ├── pima_cache.csv       # Cached PIMA dataset
│   ├── .env                 # Groq API key
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── Dashboard.jsx           # Live vitals + dual score bars
│           ├── Chart.jsx               # Real-time trend chart
│           ├── AdvancedSimulation.jsx   # Full clinical simulation panel
│           └── SimulationChart.jsx      # Projected vitals (2×2 area charts)
└── README.md
```

---

## ⚕️ Disclaimer

This system is a simulation tool for **educational and research purposes only**. It does not provide medical diagnoses. Always consult a qualified healthcare professional for medical advice, diagnosis, or treatment decisions.

---

*Built as a startup-grade prototype demonstrating how AI-powered digital twins can transform preventive healthcare.*
