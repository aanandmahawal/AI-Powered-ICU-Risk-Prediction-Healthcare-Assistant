"""
ward.py - ICU risk assessment for several patients at once.

Patients can be typed into an editable table or loaded from a CSV / Excel file (a template is
provided). Every valid row is scored by the same XGBoost model and NEWS2 as a single patient;
results are ranked by risk, can be downloaded, and any patient can be opened in full detail
and discussed with MedAssist AI.
"""

import re
import time

import pandas as pd
import streamlit as st

from clinical import CONSCIOUSNESS_LEVELS, FEATURES, FEATURE_KEYS
from predictor import format_prob, predict_patient, render_result
from styles import render_html

F = {f["key"]: f for f in FEATURES}
MAX_PATIENTS = 500

# Table columns: patient name / ID followed by the model inputs.
COLUMNS = ["Patient"] + FEATURE_KEYS

# Accepted spellings of each column in uploaded files (compared lower-case, letters/digits only).
ALIASES = {
    "Patient": ["patient", "name", "patientname", "patientid", "id", "mrn", "bed"],
    "Age": ["age", "ageyears", "years"],
    "HR": ["hr", "heartrate", "heartratebpm", "pulse", "pulserate"],
    "SBP": ["sbp", "systolic", "systolicbp", "systolicbpmmhg", "systolicbloodpressure"],
    "DBP": ["dbp", "diastolic", "diastolicbp", "diastolicbpmmhg", "diastolicbloodpressure"],
    "RespRate": ["resprate", "rr", "respiratoryrate", "respiratoryratebpm", "respirations"],
    "SpO2": ["spo2", "spo2percent", "oxygensaturation", "o2sat", "sats"],
    "Temp": ["temp", "temperature", "temperaturef", "tempf", "temperaturec", "tempc", "bodytemperature"],
    "SuppO2": ["suppo2", "supplementaloxygen", "onoxygen", "oxygen", "o2", "onsupplementaloxygen"],
    "Consciousness": ["consciousness", "levelofconsciousness", "acvpu", "avpu", "loc"],
    "ComorbidityIndex": ["comorbidityindex", "comorbidity", "comorbidities"],
}
# Optional in uploads (assumed normal / none when missing); the rest are required.
OPTIONAL_DEFAULTS = {"SuppO2": 0, "Consciousness": "Alert", "ComorbidityIndex": 0}

SAMPLE_WARD = [
    ["Bed 1 · A. Sharma", 34, 78, 118, 76, 14, 99, 98.4, False, "Alert", 0],
    ["Bed 2 · R. Kumar", 58, 96, 148, 94, 18, 97, 98.9, False, "Alert", 2],
    ["Bed 3 · M. Fernandes", 72, 112, 98, 62, 24, 92, 101.8, True, "Alert", 3],
    ["Bed 4 · S. Iyer", 81, 128, 86, 50, 28, 89, 103.1, True, "New confusion", 4],
    ["Bed 5 · P. Singh", 45, 88, 132, 86, 16, 98, 99.1, False, "Alert", 1],
]


def _empty_row(i):
    return [f"Patient {i}"] + [F[k]["default"] if k not in ("SuppO2", "Consciousness")
                               else (False if k == "SuppO2" else "Alert") for k in FEATURE_KEYS]


def _frame(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def template_csv():
    return _frame(SAMPLE_WARD).assign(SuppO2=lambda d: d["SuppO2"].astype(int)).to_csv(index=False).encode()


# ===================================================
# FILE UPLOAD
# ===================================================

def _norm(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _consciousness(v):
    if pd.isna(v):
        return "Alert"
    s = _norm(str(v).split(".")[0]) if str(v).replace(".", "", 1).isdigit() else _norm(v)
    if s.isdigit():                                   # numeric codes 0-4
        return CONSCIOUSNESS_LEVELS[int(s)] if int(s) < len(CONSCIOUSNESS_LEVELS) else None
    for level in CONSCIOUSNESS_LEVELS:
        if _norm(level) == s:
            return level
    return {"a": "Alert", "c": "New confusion", "confusion": "New confusion", "confused": "New confusion",
            "v": "Responds to voice", "voice": "Responds to voice", "p": "Responds to pain",
            "pain": "Responds to pain", "u": "Unresponsive"}.get(s, None)


def _yes_no(v):
    if pd.isna(v):
        return False
    return _norm(v) in ("1", "10", "yes", "y", "true", "t", "on")


def read_upload(file):
    """Reads an uploaded CSV / Excel file into the table format. Returns (df, notes)."""
    name = file.name.lower()
    raw = pd.read_excel(file) if name.endswith((".xlsx", ".xls")) else pd.read_csv(file)
    raw = raw.dropna(how="all")

    lookup = {_norm(c): c for c in raw.columns}
    mapping, missing = {}, []
    for col, names in ALIASES.items():
        found = next((lookup[n] for n in names if n in lookup), None)
        if found is not None:
            mapping[col] = found
        elif col != "Patient" and col not in OPTIONAL_DEFAULTS:
            missing.append(F[col]["label"])
    if missing:
        raise ValueError("The file is missing these columns: " + ", ".join(missing)
                         + ". Download the template to see the expected format.")

    notes = []
    df = pd.DataFrame(index=raw.index)
    df["Patient"] = raw[mapping["Patient"]].astype(str) if "Patient" in mapping else [
        f"Patient {i + 1}" for i in range(len(raw))]
    for k in FEATURE_KEYS:
        if k in mapping:
            df[k] = raw[mapping[k]]
        else:
            df[k] = OPTIONAL_DEFAULTS[k]
            notes.append(f"No {F[k]['label'].lower()} column: assumed "
                         f"{'none' if k != 'Consciousness' else 'Alert'} for every patient.")

    for k in ["Age", "HR", "SBP", "DBP", "RespRate", "SpO2", "Temp", "ComorbidityIndex"]:
        df[k] = pd.to_numeric(df[k], errors="coerce")
    # Temperatures written in °C (e.g. 37.2) are converted to °F.
    if df["Temp"].dropna().between(25, 45).all() and df["Temp"].notna().any():
        df["Temp"] = (df["Temp"] * 9 / 5 + 32).round(1)
        notes.append("Temperatures were in °C and have been converted to °F.")
    df["SuppO2"] = df["SuppO2"].map(_yes_no)
    df["Consciousness"] = df["Consciousness"].map(_consciousness)

    if len(df) > MAX_PATIENTS:
        notes.append(f"Only the first {MAX_PATIENTS} of {len(df)} patients were loaded.")
        df = df.head(MAX_PATIENTS)
    return df.reset_index(drop=True), notes


# ===================================================
# VALIDATION + ASSESSMENT
# ===================================================

def validate(df):
    """Splits the table into valid patient dicts and a list of problems (one per bad row)."""
    patients, problems = [], []
    for i, row in df.iterrows():
        name = str(row["Patient"]).strip() if pd.notna(row["Patient"]) and str(row["Patient"]).strip() else f"Row {i + 1}"
        issues = []
        values = {}
        for k in FEATURE_KEYS:
            v = row[k]
            if k == "Consciousness":
                if v not in CONSCIOUSNESS_LEVELS:
                    issues.append("level of consciousness not recognised")
                    continue
                values[k] = CONSCIOUSNESS_LEVELS.index(v)
            elif k == "SuppO2":
                values[k] = int(bool(v)) if pd.notna(v) else 0
            elif pd.isna(v):
                issues.append(f"{F[k]['label'].lower()} missing")
            elif not F[k]["min"] <= float(v) <= F[k]["max"]:
                issues.append(f"{F[k]['label'].lower()} {v:g} outside {F[k]['min']}-{F[k]['max']}")
            else:
                values[k] = round(float(v), 1) if k == "Temp" else int(round(float(v)))
        if not issues and values["DBP"] >= values["SBP"]:
            issues.append("diastolic BP must be lower than systolic BP")
        if issues:
            problems.append(f"**{name}**: " + "; ".join(issues))
        else:
            patients.append((name, values))
    return patients, problems


def assess(clf, meta, patients):
    results, seen = [], {}
    for name, values in patients:
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:                      # keep names unique for the patient picker
            name = f"{name} ({seen[name]})"
        p = predict_patient(clf, values, meta)
        p["name"] = name
        results.append(p)
    return sorted(results, key=lambda p: (p["prob"], p["news2"]), reverse=True)


def priority(p):
    if p["band"] == "Critical" or p["news2"] >= 7:
        return "🔴 Urgent"
    if p["band"] == "High" or p["news2"] >= 5 or p["news2_red_flags"]:
        return "🟠 Prompt review"
    if p["band"] == "Moderate":
        return "🟡 Monitor closely"
    return "🟢 Routine"


def results_frame(results):
    return pd.DataFrame([{
        "Patient": p["name"],
        "Priority": priority(p),
        "ICU risk": round(p["prob"] * 100, 1),
        "Risk band": p["band"],
        "NEWS2": p["news2"],
        "Key concern": (p["flags"][0].split(" ", 1)[1] if p["flags"] else "None"),
        "Age": p["Age"],
        "HR": p["HR"],
        "BP": f"{p['SBP']}/{p['DBP']}",
        "RR": p["RespRate"],
        "SpO₂": p["SpO2"],
        "Temp °F": p["Temp"],
    } for p in results])


# ===================================================
# UI
# ===================================================

def _set_table(df):
    st.session_state.ward_table = df
    st.session_state.ward_version = st.session_state.get("ward_version", 0) + 1


def _load_sample():
    _set_table(_frame(SAMPLE_WARD))


def _clear_table():
    _set_table(_frame([_empty_row(1)]))


def render_ward(clf, meta):
    if "ward_table" not in st.session_state:
        _set_table(_frame(SAMPLE_WARD))

    st.markdown('<div class="form-section">🏥 Patients</div>', unsafe_allow_html=True)
    st.caption("Edit the table directly, add rows with ➕, or load a CSV / Excel file. "
               f"Up to {MAX_PATIENTS} patients.")

    with st.expander("📂 Load patients from a file"):
        up = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"], key="ward_upload",
                              label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load file", icon=":material/upload:", disabled=up is None, width="stretch"):
                try:
                    df, notes = read_upload(up)
                    _set_table(df)
                    st.session_state.ward_notes = [f"Loaded {len(df)} patients from {up.name}."] + notes
                    st.session_state.pop("ward_results", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        with c2:
            st.download_button("Download template", template_csv(), "riskcare_patients_template.csv",
                               "text/csv", icon=":material/download:", width="stretch")
        st.caption("Columns: Patient, Age, HR, SBP, DBP, RespRate, SpO2, Temp (°F or °C), "
                   "SuppO2 (yes/no), Consciousness (Alert / New confusion / Responds to voice / "
                   "Responds to pain / Unresponsive), ComorbidityIndex (0-5). Common alternative "
                   "names such as 'heart_rate_bpm' are recognised.")

    for note in st.session_state.pop("ward_notes", []):
        st.info(note)

    edited = st.data_editor(
        st.session_state.ward_table,
        key=f"ward_editor_{st.session_state.ward_version}",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Patient": st.column_config.TextColumn("Patient", help="Name, ID or bed number", width="medium"),
            "Age": st.column_config.NumberColumn("Age", min_value=18, max_value=100, step=1),
            "HR": st.column_config.NumberColumn("HR", help="Heart rate (bpm)", min_value=30, max_value=200, step=1),
            "SBP": st.column_config.NumberColumn("SBP", help="Systolic BP (mmHg)", min_value=50, max_value=250, step=1),
            "DBP": st.column_config.NumberColumn("DBP", help="Diastolic BP (mmHg)", min_value=30, max_value=150, step=1),
            "RespRate": st.column_config.NumberColumn("RR", help="Respiratory rate (breaths/min)",
                                                      min_value=5, max_value=50, step=1),
            "SpO2": st.column_config.NumberColumn("SpO₂ %", min_value=70, max_value=100, step=1),
            "Temp": st.column_config.NumberColumn("Temp °F", min_value=90.0, max_value=110.0, step=0.1,
                                                  format="%.1f"),
            "SuppO2": st.column_config.CheckboxColumn("On O₂", help="Receiving supplemental oxygen"),
            "Consciousness": st.column_config.SelectboxColumn("Consciousness", options=CONSCIOUSNESS_LEVELS,
                                                              required=True, width="medium"),
            "ComorbidityIndex": st.column_config.NumberColumn("Comorb.", help="Comorbidity index 0-5",
                                                              min_value=0, max_value=5, step=1),
        },
    )

    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        run = st.button(f"🚨 Assess {len(edited)} patient{'s' if len(edited) != 1 else ''}",
                        type="primary", width="stretch", disabled=len(edited) == 0)
    with b2:
        st.button("Sample ward", icon=":material/group:", on_click=_load_sample, width="stretch",
                  help="Load five example patients")
    with b3:
        st.button("Clear table", icon=":material/delete_sweep:", on_click=_clear_table, width="stretch")

    if run:
        if len(edited) > MAX_PATIENTS:
            st.error(f"❌ Please assess at most {MAX_PATIENTS} patients at a time.")
        else:
            patients, problems = validate(edited)
            with st.status(f"Assessing {len(patients)} patients...", expanded=True) as status:
                bar = st.progress(0)
                for i, step in enumerate(["Validating patient data", "Running the ICU risk model",
                                          "Calculating early warning scores", "Ranking patients by risk"]):
                    st.markdown(f'<div class="analysis-step"><span class="tick">✓</span>{step}</div>',
                                unsafe_allow_html=True)
                    if i == 1:
                        st.session_state.ward_results = assess(clf, meta, patients)
                        st.session_state.ward_problems = problems
                    time.sleep(0.4)
                    bar.progress((i + 1) / 4)
                status.update(label=f"Assessment complete · {len(patients)} patients",
                              state="complete", expanded=False)
            # The highest-risk patient becomes the chatbot's current patient.
            results = st.session_state.ward_results
            st.session_state.ward_pick = results[0]["name"] if results else None

    if st.session_state.get("ward_results") is not None:
        render_ward_results(st.session_state.ward_results, st.session_state.get("ward_problems", []))
    else:
        st.session_state.pop("patient", None)


def render_ward_results(results, problems):
    if problems:
        with st.expander(f"⚠️ {len(problems)} row(s) skipped, please correct them", expanded=True):
            st.markdown("\n".join(f"- {p}" for p in problems))
    if not results:
        st.warning("No valid patients to assess.")
        return

    st.markdown('<div class="section-title">📊 Ward overview</div>', unsafe_allow_html=True)

    counts = {b: sum(p["band"] == b for p in results) for b in ["Critical", "High", "Moderate", "Low"]}
    urgent = sum(priority(p).endswith("Urgent") for p in results)
    tiles = "".join(
        f'<div class="ward-tile band-{b.lower()}"><span class="n">{counts[b]}</span><span class="l">{b} risk</span></div>'
        for b in counts
    )
    render_html(
        f"""
        <div class="ward-tiles">
            <div class="ward-tile total"><span class="n">{len(results)}</span><span class="l">Patients</span></div>
            {tiles}
        </div>
        <div class="ward-note">{urgent} patient{'s' if urgent != 1 else ''} need{'s' if urgent == 1 else ''} urgent review ·
        ranked by ICU risk, highest first</div>
        """
    )

    df = results_frame(results)
    st.dataframe(
        df, hide_index=True, width="stretch",
        column_config={
            "ICU risk": st.column_config.ProgressColumn("ICU risk", format="%.1f%%", min_value=0, max_value=100),
            "Key concern": st.column_config.TextColumn("Key concern", width="medium"),
        },
    )
    st.download_button("Download results (CSV)", df.to_csv(index=False).encode(), "riskcare_ward_assessment.csv",
                       "text/csv", icon=":material/download:")

    st.markdown('<div class="section-title">🔎 Patient detail</div>', unsafe_allow_html=True)
    names = [p["name"] for p in results]
    if st.session_state.get("ward_pick") not in names:
        st.session_state.ward_pick = names[0]
    pick = st.selectbox(
        "Patient", names, key="ward_pick", label_visibility="collapsed",
        format_func=lambda n: next(f"{n} · {format_prob(p['prob']).replace('&lt;', '<').replace('&gt;', '>')} "
                                   f"· {p['band']} risk" for p in results if p["name"] == n),
    )
    chosen = next(p for p in results if p["name"] == pick)
    # The selected patient is the one MedAssist AI personalises its answers to.
    st.session_state.patient = chosen
    render_result(chosen)
