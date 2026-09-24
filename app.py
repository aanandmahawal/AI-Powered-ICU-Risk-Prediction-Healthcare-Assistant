from html import escape

import streamlit as st

from predictor import F, streamlit_predict_custom_input, load_model, format_prob
from chatbot import (
    GROQ_MODEL_LABEL, get_api_key, get_medical_response, save_api_key, validate_api_key,
)
from reports import MAX_FILES, REPORT_FILE_TYPES, process_uploads
from styles import load_css, render_html, render_message
from ward import render_ward

GENERAL_SUGGESTIONS = [
    "What are symptoms of diabetes?",
    "Explain hypertension.",
    "How can I improve heart health?",
]

PATIENT_SUGGESTIONS = [
    "How can I keep these vitals in a healthy range?",
    "Explain this ICU risk result in simple words.",
    "Suggest diet and lifestyle tips for these vitals.",
]

WARD_SUGGESTIONS = [
    "Which patients need attention first, and why?",
    "Summarise the ward's overall risk.",
    "How can I keep this patient's vitals in a healthy range?",
]

SINGLE, MULTIPLE = "Single patient", "Multiple patients"

# Chat window sizes: "docked" = side panel, "full" = whole page, "minimized" = floating button
DOCKED, FULL, MINIMIZED = "docked", "full", "minimized"

# ===================================================
# PAGE CONFIG
# ===================================================

st.set_page_config(
    page_title="AI Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================
# LOAD CSS
# ===================================================

st.markdown(load_css(), unsafe_allow_html=True)

# ===================================================
# SESSION STATE
# ===================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_reply" not in st.session_state:
    st.session_state.awaiting_reply = False

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = DOCKED

if "groq_key" not in st.session_state:
    st.session_state.groq_key = None

if "reports" not in st.session_state:
    st.session_state.reports = []          # medical reports accepted in this conversation

if "pending_files" not in st.session_state:
    st.session_state.pending_files = []    # files attached to the message awaiting a reply

if "predict_mode" not in st.session_state:
    st.session_state.predict_mode = SINGLE

# ===================================================
# LOAD MODEL
# ===================================================

try:
    clf, meta = load_model()
except Exception as e:
    clf, meta = None, None
    st.error(f"Model could not be loaded ({e}). Run `python train_model.py` to build it.")

api_key = get_api_key(st.session_state.groq_key)

# The key can only be saved to .env when the app is opened on this computer,
# so a visitor on the network can never overwrite it.
host = st.context.headers.get("Host", "").split(":")[0]
is_local = host in ("localhost", "127.0.0.1")

# ===================================================
# CALLBACKS
# (run before the rerun, so state is already updated when the page draws)
# ===================================================

def send_prompt(text, files=None):
    message = {
        "role": "user",
        "content": text
    }
    if files:
        message["files"] = [f["name"] for f in files]
        st.session_state.pending_files = files
    st.session_state.messages.append(message)
    st.session_state.awaiting_reply = True
    # Answers are easier to read full-page; the user can shrink it back at any time.
    st.session_state.chat_mode = FULL


def on_chat_submit():
    value = st.session_state.get("chat_prompt")
    if value is None:
        return
    text = (value.text if hasattr(value, "text") else value) or ""
    files = [
        {"name": f.name, "data": f.getvalue()}
        for f in (getattr(value, "files", None) or [])[:MAX_FILES]
    ]
    if text.strip() or files:
        send_prompt(text.strip(), files)


def clear_chat():
    st.session_state.messages = []
    st.session_state.awaiting_reply = False
    st.session_state.reports = []
    st.session_state.pending_files = []


def use_report_vitals(vitals):
    """Copies vital signs found in a report into the single-patient form."""
    for key, value in vitals.items():
        value = min(max(value, F[key]["min"]), F[key]["max"])
        st.session_state[f"in_{key}"] = round(float(value), 1) if key == "Temp" else int(round(value))
    st.session_state.predict_mode = SINGLE
    st.session_state.chat_mode = DOCKED
    st.session_state.vitals_from_report = True


def set_chat_mode(mode):
    st.session_state.chat_mode = mode

# ===================================================
# SIDEBAR
# ===================================================

with st.sidebar:

    render_html(
        """
        <div class="brand">
            <div class="brand-logo">🏥</div>
            <div>
                <div class="brand-name">RiskCare</div>
                <div class="brand-tag">ICU risk &amp; health assistant</div>
            </div>
        </div>
        <div class="side-card">
            <div class="side-title">How it works</div>
            <div class="step"><span>1</span>Enter one patient's vital signs, or several patients in a table or file.</div>
            <div class="step"><span>2</span>The AI model estimates each patient's ICU admission risk.</div>
            <div class="step"><span>3</span>Ask MedAssist AI for tailored guidance, or attach a medical report for a plain-language review.</div>
        </div>
        """
    )

    status = (
        f"<span class='dot on'></span>Connected · {GROQ_MODEL_LABEL}"
        if api_key else
        "<span class='dot off'></span>Not connected"
    )

    render_html(
        f"""
        <div class="side-card">
            <div class="side-title">AI assistant</div>
            <div class="side-status">{status}</div>
        </div>
        <div class="side-disclaimer">
            ⚠️ For educational and demonstration purposes only. Not designed to
            diagnose, treat, prescribe, or replace professional medical consultation.
        </div>
        <div class="side-footer">Built with Streamlit, XGBoost and Groq</div>
        """
    )

# ===================================================
# HEADER
# ===================================================

render_html(
    """
    <div class="main-title">🏥 AI Healthcare Assistant</div>
    <div class="subtitle">ICU Risk Prediction with a Personalised Medical AI Assistant</div>
    """
)

# ===================================================
# MEDICAL AI ASSISTANT
# ===================================================

def chat_height(full):
    """
    Height of the message area. It grows with the conversation (so the input box sits right
    under the latest message) and stops growing at a comfortable maximum, after which the
    messages scroll.
    """
    chars_per_line = 120 if full else 42
    height = 40
    msgs = st.session_state.messages
    if not msgs:
        height += 150 + 110 + 3 * 52    # greeting + report hint + suggested questions
    for m in msgs:
        text = m["content"]
        lines = sum(max(1, -(-len(line) // chars_per_line)) for line in text.split("\n"))
        height += 44 + 26 * lines + 34 * len(m.get("files", []))
    if st.session_state.awaiting_reply:
        height += 90
    maximum = 520 if full else 440
    return int(min(max(height, 220), maximum))


def render_chat(full):
    mode_key = "chat_panel_full" if full else "chat_panel"

    with st.container(key=mode_key):

        patient = st.session_state.get("patient")

        with st.container(horizontal=True, vertical_alignment="center", wrap=False, key="chat_head"):
            render_html(
                f"""
                <div class="chat-header">
                    <div class="chat-avatar">🩺</div>
                    <div>
                        <div class="chat-title">MedAssist AI</div>
                        <div class="chat-status">
                            <span class="dot {'on' if api_key else 'off'}"></span>{'Online' if api_key else 'Setup needed'}
                        </div>
                    </div>
                </div>
                """,
                width="stretch"
            )
            st.button(
                "",
                icon=":material/refresh:",
                help="New conversation",
                key="clear_chat",
                on_click=clear_chat,
                type="tertiary"
            )
            st.button(
                "",
                icon=":material/close_fullscreen:" if full else ":material/open_in_full:",
                help="Restore to side panel" if full else "Expand to full page",
                key="resize_chat",
                on_click=set_chat_mode,
                args=(DOCKED if full else FULL,),
                type="tertiary"
            )
            st.button(
                "",
                icon=":material/remove:",
                help="Minimize",
                key="close_chat",
                on_click=set_chat_mode,
                args=(MINIMIZED,),
                type="tertiary"
            )

        # ---------- Groq API key setup ----------

        if not api_key:

            render_html(
                """
                <div class="setup-card">
                    <div class="setup-title">🔑 Connect the AI assistant</div>
                    MedAssist AI runs on Groq's free API. Get a key at
                    <a href="https://console.groq.com/keys" target="_blank">console.groq.com/keys</a>
                    (sign in → <b>Create API Key</b>) and paste it below.
                </div>
                """
            )

            with st.form("groq_setup", border=False):
                key_input = st.text_input(
                    "Groq API key",
                    type="password",
                    placeholder="gsk_...",
                    label_visibility="collapsed"
                )
                remember = st.checkbox(
                    "Remember on this computer (saves to .env)",
                    value=True,
                    disabled=not is_local,
                    help=None if is_local else "Only available when the app is opened on the host computer."
                )
                connect = st.form_submit_button("Connect", width="stretch")

            if connect:
                key_input = key_input.strip()
                if not key_input:
                    st.error("Please paste your Groq API key.")
                else:
                    with st.spinner("Checking key with Groq..."):
                        ok, msg = validate_api_key(key_input)
                    if ok:
                        st.session_state.groq_key = key_input
                        if remember and is_local:
                            save_api_key(key_input)
                        st.rerun()
                    else:
                        st.error(msg)

        # ---------- Patient context ----------

        ward = (st.session_state.get("ward_results")
                if st.session_state.predict_mode == MULTIPLE else None)

        if patient:
            who = escape(patient.get("name") or "current patient")
            ward_line = (f"<div class='pc-ward'>🏥 Also aware of all {len(ward)} assessed patients</div>"
                         if ward else "")
            render_html(
                f"""
                <div class="patient-context">
                    <div class="pc-title">
                        🧾 Personalised to {who}
                        <span class="band-pill band-{patient['band_css']}">{format_prob(patient['prob'])} · {patient['band']} risk</span>
                    </div>
                    <div class="pc-vitals">
                        {patient['Age']} y · HR {patient['HR']} · BP {patient['SBP']}/{patient['DBP']}
                        · RR {patient['RespRate']} · SpO₂ {patient['SpO2']}% · {patient['Temp']}°F
                        · NEWS2 {patient['news2']}
                    </div>
                    {ward_line}
                </div>
                """
            )

        elif api_key:
            render_html(
                """
                <div class="patient-context general">
                    💬 General medical mode. Enter vitals and click
                    <b>Predict ICU Risk</b> to get advice personalised to the patient.
                </div>
                """
            )

        # ---------- Reports on file ----------

        reports = st.session_state.reports

        if reports:
            items = "".join(
                f"<div class='rc-item'>📄 <b>{escape(r['name'])}</b><span>{escape(r['type'])}</span></div>"
                for r in reports
            )
            render_html(f"<div class='report-card'><div class='rc-title'>Medical reports in this conversation</div>{items}</div>")

            vitals = next((r["vitals"] for r in reversed(reports) if r["vitals"]), None)
            if vitals:
                st.button(
                    "Use the report's vitals in the ICU predictor",
                    icon=":material/input:",
                    help="Fills in: " + ", ".join(F[k]["label"] for k in vitals),
                    key="use_report_vitals",
                    on_click=use_report_vitals,
                    args=(vitals,),
                    width="stretch"
                )

        # ---------- Conversation ----------

        if api_key:

            # Scrolls to the newest message; the welcome screen starts at the top.
            chat_box = st.container(height=chat_height(full), key="chat_box",
                                    autoscroll=bool(st.session_state.messages))

            with chat_box:

                if len(st.session_state.messages) == 0:

                    with st.chat_message("assistant"):
                        if ward:
                            st.markdown(
                                f"Hi! I can see the assessment of all {len(ward)} patients. Ask me who "
                                "needs attention first, about any one patient, or attach a medical report."
                            )
                        elif patient:
                            st.markdown(
                                "Hi! I can see the patient's latest assessment. Ask me what the "
                                "values mean or how to keep them healthy, or attach a medical report "
                                "for a plain-language review."
                            )
                        else:
                            st.markdown(
                                "Hi! I'm MedAssist AI. Ask me any medical question, run an ICU risk "
                                "prediction for advice tailored to the patient, or attach a medical report."
                            )

                    render_html(
                        """
                        <div class="upload-hint">
                            <span>📎</span>
                            <div><b>Have a medical report?</b> Attach it with the clip icon in the
                            message box: lab results, imaging, ECG, discharge summaries or
                            prescriptions, as a PDF, photo, Word or text file.</div>
                        </div>
                        """
                    )

                    st.caption("Suggested questions")

                    suggestions = (WARD_SUGGESTIONS if ward else
                                   PATIENT_SUGGESTIONS if patient else GENERAL_SUGGESTIONS)

                    for i, s in enumerate(suggestions):
                        st.button(
                            s,
                            key=f"suggestion_{i}",
                            on_click=send_prompt,
                            args=(s,),
                            width="stretch"
                        )

                for msg in st.session_state.messages:

                    with st.chat_message(msg["role"]):
                        if msg.get("files"):
                            render_html("".join(
                                f"<div class='file-chip'>📄 {escape(name)}</div>" for name in msg["files"]
                            ))
                        if msg["content"]:
                            render_message(msg["content"])

                if st.session_state.awaiting_reply:

                    with st.chat_message("assistant"):

                        files = st.session_state.pending_files

                        if files:
                            with st.status("Reviewing the document...", expanded=True) as status:
                                response, accepted = process_uploads(
                                    files,
                                    st.session_state.messages[-1]["content"],
                                    patient,
                                    st.session_state.groq_key,
                                    on_step=lambda text: st.markdown(
                                        f'<div class="analysis-step"><span class="tick">✓</span>{escape(text)}</div>',
                                        unsafe_allow_html=True
                                    )
                                )
                                status.update(
                                    label="Report reviewed" if accepted else "Review complete",
                                    state="complete",
                                    expanded=False
                                )
                            st.session_state.reports.extend(accepted)
                            st.session_state.pending_files = []

                        else:
                            accepted = []
                            with st.spinner(
                                "🩺 Analyzing your question..."
                            ):

                                response = get_medical_response(
                                    st.session_state.messages,
                                    patient,
                                    st.session_state.groq_key,
                                    reports=st.session_state.reports,
                                    ward=ward
                                )

                        render_message(response)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response
                        }
                    )
                    st.session_state.awaiting_reply = False

                    # A newly accepted report is listed above the conversation: redraw to show it.
                    if accepted:
                        st.rerun()

            st.chat_input(
                "Ask a medical question or attach a report...",
                key="chat_prompt",
                accept_file="multiple",
                file_type=REPORT_FILE_TYPES,
                on_submit=on_chat_submit
            )

        render_html(
            """
            <div class="chat-disclaimer">
            ⚠️ Educational information only. Consult qualified healthcare
            professionals for diagnosis or treatment decisions.
            </div>
            """
        )

# ===================================================
# ICU RISK PREDICTOR
# ===================================================

def render_predictor():
    grid = ""
    if meta:
        facts = [
            ("Algorithm", "XGBoost"),
            ("Trees", f"{meta['n_trees']}"),
            ("Max depth", f"{meta['params']['max_depth']}"),
            ("ROC-AUC", f"{meta['test_metrics']['cv_roc_auc_mean']:.2f}"),
            ("Patients", f"{meta['n_patients']:,}"),
            ("Parameters", f"{len(meta['features'])}"),
        ]
        grid = '<div class="model-grid">' + "".join(
            f'<div><span class="k">{k}</span><span class="v">{v}</span></div>' for k, v in facts
        ) + "</div>"

    render_html(
        f"""
        <div class="health-card">
        <h3>📈 ICU Risk Prediction</h3>
        <p>Estimate the probability that a patient will need ICU admission from their vital signs and clinical profile.</p>
        {grid}
        </div>
        """
    )

    if clf is not None:

        mode = st.segmented_control(
            "Assessment",
            [SINGLE, MULTIPLE],
            key="predict_mode",
            required=True,
            label_visibility="collapsed",
            format_func=lambda m: ("👤 " if m == SINGLE else "👥 ") + m,
        )

        if mode == MULTIPLE:
            render_ward(clf, meta)
        else:
            if st.session_state.pop("vitals_from_report", False):
                st.info("📄 Vital signs from the uploaded report have been filled in. Complete the "
                        "patient profile, check the values and click **Predict ICU Risk**.")
            streamlit_predict_custom_input(clf, meta)

# ===================================================
# LAYOUT
# ===================================================

mode = st.session_state.chat_mode

if mode == FULL:
    render_chat(full=True)
    # Still rendered (so the form keeps its values) but hidden while the chat is full-page.
    with st.container(key="predictor_hidden"):
        render_predictor()

elif mode == DOCKED:
    left, right = st.columns([3, 2], gap="large")
    with left:
        render_predictor()
    with right:
        render_chat(full=False)

else:
    render_predictor()
    st.button(
        "Ask MedAssist AI",
        icon=":material/chat:",
        key="open_chat",
        on_click=set_chat_mode,
        args=(DOCKED,),
        type="primary"
    )
