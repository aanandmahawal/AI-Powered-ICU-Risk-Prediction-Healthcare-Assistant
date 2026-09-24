"""
clinical.py - shared clinical definitions used by the app, the model and the training script.

- FEATURES: the model inputs (order matters: it is the column order the model is trained on)
- news2_score(): the UK Royal College of Physicians NEWS2 early-warning score, shown next to
  the model as an established clinical cross-check
- abnormal_flags(): plain-language list of vitals outside normal adult ranges
- risk_band(): maps a probability to Low / Moderate / High / Critical
"""

CONSCIOUSNESS_LEVELS = [
    "Alert",
    "New confusion",
    "Responds to voice",
    "Responds to pain",
    "Unresponsive",
]

# key, label, unit, min, max, default, step, normal (low, high) or None, help
FEATURES = [
    dict(key="Age", label="Age", unit="years", min=18, max=100, default=45, step=1,
         normal=None, help="Adult patients (18+)."),
    dict(key="HR", label="Heart Rate", unit="bpm", min=30, max=200, default=80, step=1,
         normal=(60, 100), help="Resting pulse. Normal adult range 60-100 bpm."),
    dict(key="SBP", label="Systolic BP", unit="mmHg", min=50, max=250, default=120, step=1,
         normal=(90, 140), help="Top number of the blood pressure reading."),
    dict(key="DBP", label="Diastolic BP", unit="mmHg", min=30, max=150, default=80, step=1,
         normal=(60, 90), help="Bottom number of the blood pressure reading."),
    dict(key="RespRate", label="Respiratory Rate", unit="breaths/min", min=5, max=50, default=16, step=1,
         normal=(12, 20), help="Breaths per minute at rest."),
    dict(key="SpO2", label="Oxygen Saturation (SpO₂)", unit="%", min=70, max=100, default=98, step=1,
         normal=(95, 100), help="Pulse-oximeter reading."),
    dict(key="Temp", label="Body Temperature", unit="°F", min=90.0, max=110.0, default=98.6, step=0.1,
         normal=(97.0, 100.4), help="In °F (98.6 °F = 37 °C). Fever is above 100.4 °F (38 °C)."),
    dict(key="SuppO2", label="On Supplemental Oxygen", unit="", min=0, max=1, default=0, step=1,
         normal=None, help="Patient is receiving oxygen by mask or nasal cannula."),
    dict(key="Consciousness", label="Level of Consciousness", unit="", min=0, max=4, default=0, step=1,
         normal=None, help="ACVPU scale: Alert, new Confusion, responds to Voice, to Pain, Unresponsive."),
    dict(key="ComorbidityIndex", label="Comorbidity Index", unit="", min=0, max=5, default=1, step=1,
         normal=None, help="0 = no chronic illness, 5 = many severe chronic conditions "
                           "(e.g. heart failure, COPD, kidney disease, diabetes, cancer)."),
]

FEATURE_KEYS = [f["key"] for f in FEATURES]
FEATURE_LABELS = {f["key"]: f["label"] for f in FEATURES}

RISK_BANDS = [
    # upper bound (exclusive), name, css class
    (0.10, "Low", "low"),
    (0.30, "Moderate", "moderate"),
    (0.60, "High", "high"),
    (1.01, "Critical", "critical"),
]


def f_to_c(temp_f):
    return (temp_f - 32) * 5 / 9


def risk_band(prob):
    for upper, name, css in RISK_BANDS:
        if prob < upper:
            return name, css
    return RISK_BANDS[-1][1], RISK_BANDS[-1][2]


def news2_breakdown(p):
    """NEWS2 (SpO2 scale 1) points per parameter. `p` is a dict with the FEATURE_KEYS."""
    parts = {}

    rr = p["RespRate"]
    parts["RespRate"] = 3 if rr <= 8 else 1 if rr <= 11 else 0 if rr <= 20 else 2 if rr <= 24 else 3

    s = p["SpO2"]
    parts["SpO2"] = 3 if s <= 91 else 2 if s <= 93 else 1 if s <= 95 else 0

    parts["SuppO2"] = 2 if p["SuppO2"] else 0

    sbp = p["SBP"]
    parts["SBP"] = 3 if sbp <= 90 else 2 if sbp <= 100 else 1 if sbp <= 110 else 0 if sbp <= 219 else 3

    hr = p["HR"]
    parts["HR"] = 3 if hr <= 40 else 1 if hr <= 50 else 0 if hr <= 90 else 1 if hr <= 110 else 2 if hr <= 130 else 3

    parts["Consciousness"] = 3 if p["Consciousness"] > 0 else 0

    t = f_to_c(p["Temp"])
    parts["Temp"] = 3 if t <= 35.0 else 1 if t <= 36.0 else 0 if t <= 38.0 else 1 if t <= 39.0 else 2

    return parts


def news2_score(p):
    """NEWS2 total. Returns (total, parameters_scoring_3, clinical_risk)."""
    parts = news2_breakdown(p)
    total = sum(parts.values())
    red_flags = [k for k, v in parts.items() if v == 3]

    if total >= 7:
        clinical_risk = "High"
    elif total >= 5:
        clinical_risk = "Medium"
    elif red_flags:
        clinical_risk = "Low-medium"
    else:
        clinical_risk = "Low"

    return total, red_flags, clinical_risk


def abnormal_flags(p):
    """Plain-language list of findings outside normal adult ranges."""
    flags = []

    for f in FEATURES:
        if f["normal"] is None:
            continue
        v = p[f["key"]]
        lo, hi = f["normal"]
        if v < lo:
            flags.append(f"🔻 Low {f['label']}: {v} {f['unit']} (normal {lo}-{hi})")
        elif v > hi:
            flags.append(f"🔺 High {f['label']}: {v} {f['unit']} (normal {lo}-{hi})")

    if p["SuppO2"]:
        flags.append("🫁 Receiving supplemental oxygen")
    if p["Consciousness"] > 0:
        flags.append(f"🧠 Reduced consciousness: {CONSCIOUSNESS_LEVELS[p['Consciousness']]}")
    if p["ComorbidityIndex"] >= 3:
        flags.append(f"⚠️ High comorbidity burden: {p['ComorbidityIndex']} / 5")
    if p["Age"] >= 75:
        flags.append(f"👴 Advanced age: {p['Age']} years")

    return flags
