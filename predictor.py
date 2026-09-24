import json
import time

import pandas as pd
import streamlit as st
import xgboost as xgb

from styles import render_html
from clinical import (
    CONSCIOUSNESS_LEVELS, FEATURES, FEATURE_KEYS, FEATURE_LABELS,
    abnormal_flags, news2_breakdown, news2_score, risk_band,
)

MODEL_PATH = "model/icu_xgb_model.json"
META_PATH = "model/model_meta.json"

F = {f["key"]: f for f in FEATURES}


@st.cache_resource
def load_model():
    """Loads the XGBoost model once for all sessions. Returns (model, meta)."""
    clf = xgb.XGBClassifier()
    clf.load_model(MODEL_PATH)
    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    return clf, meta


def predict_patient(clf, values, meta):
    """
    Returns probability, per-feature contributions (log-odds, from XGBoost's built-in
    SHAP values) and the NEWS2 cross-check for one patient.
    """
    X = pd.DataFrame([values])[FEATURE_KEYS]
    # The training data has no "New confusion" level; score it like "Responds to voice",
    # as ACVPU / NEWS2 do.
    if X.loc[0, "Consciousness"] == 1:
        X.loc[0, "Consciousness"] = 2
    prob = float(clf.predict_proba(X)[0][1])

    contribs = clf.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]
    drivers = sorted(
        (
            {"key": k, "label": FEATURE_LABELS[k], "value": display_value(k, values[k]), "contrib": float(c)}
            for k, c in zip(FEATURE_KEYS, contribs)
        ),
        key=lambda d: abs(d["contrib"]),
        reverse=True,
    )

    news2, red_flags, news2_risk = news2_score(values)
    band, band_css = risk_band(prob)

    return {
        **values,
        "prob": prob,
        "band": band,
        "band_css": band_css,
        "news2": news2,
        "news2_risk": news2_risk,
        "news2_red_flags": [FEATURE_LABELS[k] for k in red_flags],
        "news2_parts": news2_breakdown(values),
        "drivers": drivers,
        "flags": abnormal_flags(values),
    }


def display_value(key, v):
    if key == "SuppO2":
        return "Yes" if v else "No"
    if key == "Consciousness":
        return CONSCIOUSNESS_LEVELS[v]
    if key == "ComorbidityIndex":
        return f"{v} / 5"
    unit = F[key]["unit"]
    return f"{v} {unit}".strip()


def format_prob(p):
    if p >= 0.995:
        return "&gt;99%"
    if p < 0.005:
        return "&lt;1%"
    return f"{p:.0%}" if p >= 0.1 else f"{p:.1%}"


def number(key):
    f = F[key]
    is_float = isinstance(f["step"], float)
    # A value already in session state (e.g. filled in from a medical report) is used instead
    # of the default, so the default is only passed the first time.
    default = {} if f"in_{key}" in st.session_state else {"value": f["default"]}
    return st.number_input(
        f"{f['label']} ({f['unit']})",
        min_value=f["min"], max_value=f["max"], step=f["step"],
        format="%.1f" if is_float else "%d", help=f["help"], key=f"in_{key}", **default,
    )


def streamlit_predict_custom_input(clf, meta):

    with st.form("icu_form"):

        st.markdown('<div class="form-section">👤 Patient profile</div>', unsafe_allow_html=True)

        name = st.text_input("Patient name or ID (optional)", placeholder="e.g. Bed 4 · R. Kumar",
                             max_chars=60, key="in_name")

        p1, p2 = st.columns(2)
        with p1:
            age = number("Age")
            consciousness = st.selectbox(
                F["Consciousness"]["label"], range(len(CONSCIOUSNESS_LEVELS)),
                format_func=lambda i: CONSCIOUSNESS_LEVELS[i], help=F["Consciousness"]["help"],
                key="in_Consciousness",
            )
        with p2:
            comorbidity = st.slider(
                F["ComorbidityIndex"]["label"], 0, 5, value=F["ComorbidityIndex"]["default"],
                help=F["ComorbidityIndex"]["help"], key="in_ComorbidityIndex",
            )
            supp_o2 = st.toggle(F["SuppO2"]["label"], help=F["SuppO2"]["help"], key="in_SuppO2")

        st.markdown('<div class="form-section">💓 Vital signs</div>', unsafe_allow_html=True)

        v1, v2, v3 = st.columns(3)
        with v1:
            hr = number("HR")
            rr = number("RespRate")
        with v2:
            sbp = number("SBP")
            dbp = number("DBP")
        with v3:
            spo2 = number("SpO2")
            temp = number("Temp")

        submitted = st.form_submit_button("🚨 Predict ICU Risk", width="stretch")

    if submitted:
        if dbp >= sbp:
            st.error("❌ Diastolic BP must be lower than systolic BP. Please check the blood pressure values.")
        else:
            values = {
                "Age": int(age), "HR": int(hr), "SBP": int(sbp), "DBP": int(dbp),
                "RespRate": int(rr), "SpO2": int(spo2), "Temp": round(float(temp), 1),
                "SuppO2": int(supp_o2), "Consciousness": int(consciousness),
                "ComorbidityIndex": int(comorbidity),
            }
            try:
                with st.status("Analysing patient data...", expanded=True) as status:
                    bar = st.progress(0)
                    steps = [
                        "Validating vital signs",
                        "Running the ICU risk model",
                        "Calculating the early warning score",
                        "Identifying key risk factors",
                    ]
                    for i, step in enumerate(steps):
                        st.markdown(f'<div class="analysis-step"><span class="tick">✓</span>{step}</div>',
                                    unsafe_allow_html=True)
                        if i == 1:
                            # Kept in session state so the result survives reruns (e.g. chatting)
                            # and the chatbot can personalise its answers to this patient.
                            result = predict_patient(clf, values, meta)
                            result["name"] = name.strip() or None
                            st.session_state.single_result = result
                            st.session_state.patient = result
                        time.sleep(0.6)
                        bar.progress((i + 1) / len(steps))
                    status.update(label="Assessment complete", state="complete", expanded=False)
            except Exception as e:
                st.error(f"❌ Prediction failed: {str(e)}")

    result = st.session_state.get("single_result")

    if result:
        # This patient is the one MedAssist AI personalises its answers to.
        st.session_state.patient = result
        render_result(result)
    else:
        st.session_state.pop("patient", None)


def render_result(p):
    st.markdown('<div class="section-title">📊 Risk assessment</div>', unsafe_allow_html=True)

    pct = max(p["prob"] * 100, 1.5)
    red_flags = (
        f"<div class='news-flags'>⚠ Single parameter in the red zone: {', '.join(p['news2_red_flags'])}</div>"
        if p["news2_red_flags"] else ""
    )
    level = "high" if p["news2"] >= 7 else "medium" if p["news2"] >= 5 else "low"
    seg = lambda name: f"on {name}" if level == name else ""

    render_html(
        f"""
        <div class="result-grid">
            <div class="result-card band-{p['band_css']}">
                <div class="result-label">ICU admission risk</div>
                <div class="result-main">
                    <span class="result-prob">{format_prob(p['prob'])}</span>
                    <span class="band-pill band-{p['band_css']}">{p['band']} risk</span>
                </div>
                <div class="gauge"><div class="gauge-fill band-{p['band_css']}" style="width:{pct:.1f}%"></div></div>
                <div class="gauge-scale"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
            </div>
            <div class="result-card news-card">
                <div class="result-label">Early warning score (NEWS2)</div>
                <div class="result-main">
                    <span class="result-prob">{p['news2']}<span style="font-size:18px;color:#64748b;font-weight:600"> / 20</span></span>
                    <span class="band-pill news-{p['news2_risk'].lower().replace('-', '')}">{p['news2_risk']} clinical risk</span>
                </div>
                <div class="news-scale">
                    <span class="{seg('low')}">0–4 Low</span>
                    <span class="{seg('medium')}">5–6 Medium</span>
                    <span class="{seg('high')}">7+ High</span>
                </div>
                <div class="news-note">Hospital bedside score for spotting patients who are deteriorating.</div>
                {red_flags}
            </div>
        </div>
        """
    )

    with st.expander("About the early warning score"):
        rows = "\n".join(
            f"| {FEATURE_LABELS[k]} | {display_value(k, p[k])} | {v} |"
            for k, v in p["news2_parts"].items()
        )
        st.markdown(
            f"""
The **National Early Warning Score 2 (NEWS2)**, published by the UK Royal College of Physicians,
is used in hospitals to detect patients whose condition is getting worse. Each vital sign earns
0–3 points depending on how far it is from normal, and the points are added up.

| Score | Clinical risk | Recommended response |
|---|---|---|
| 0–4 | Low | Routine ward monitoring |
| Any single parameter scoring 3 | Low–medium | Urgent review by a ward clinician |
| 5–6 | Medium | Urgent review by a clinician skilled in acute illness |
| 7 or more | High | Emergency assessment by a critical-care team |

It complements the ICU risk percentage: the percentage estimates the chance of ICU admission,
while the early warning score reflects how abnormal the vital signs are right now.

**This patient's score**

| Parameter | Value | Points |
|---|---|---|
{rows}
| **Total** | | **{p['news2']}** |
            """
        )

    if p["band"] == "Critical" or p["news2"] >= 7:
        st.error("🚑 **Urgent clinical review recommended.** These findings suggest the patient may need critical care assessment now.")
    elif p["band"] == "High" or p["news2"] >= 5 or p["news2_red_flags"]:
        st.warning("⚠️ **Prompt clinical review recommended.** Increase the frequency of vital-sign monitoring.")

    st.markdown('<div class="sub-title">🩺 Clinical findings</div>', unsafe_allow_html=True)
    if p["flags"]:
        st.markdown("\n".join(f"- {f}" for f in p["flags"]))
    else:
        st.success("✅ All vital signs are within normal adult ranges.")

    st.info("💬 Ask **MedAssist AI** for guidance tailored to these vitals.")
