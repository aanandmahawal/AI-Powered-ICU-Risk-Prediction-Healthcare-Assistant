import streamlit as st
import os
import joblib

from predictor import streamlit_predict_custom_input
from chatbot import get_medical_response
from styles import load_css

MODEL_PATH = "xgb_icu_model.pkl.gz"

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

# ===================================================
# LOAD MODEL
# ===================================================

if "clf" not in st.session_state:

    if os.path.exists(MODEL_PATH):
        st.session_state.clf = joblib.load(MODEL_PATH)

    else:
        st.error("Model file not found.")

# ===================================================
# HEADER
# ===================================================

st.markdown(
    """
    <div class="main-title">
        🏥 AI Healthcare Assistant
    </div>

    <div class="subtitle">
        ICU Risk Prediction + Medical AI Chatbot
    </div>
    """,
    unsafe_allow_html=True
)

# ===================================================
# TOP NAVIGATION
# ===================================================

page = st.radio(
    "Navigation",
    [
        "📈 ICU Risk Predictor",
        "🤖 Medical AI Chatbot",
        "📖 About"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

# ===================================================
# SIDEBAR
# ===================================================

with st.sidebar:

    st.markdown("## 🏥 RiskCare")

    st.markdown("---")

    st.info(
        """
        RiskCare is an AI-powered healthcare assistant
        that combines machine learning-based ICU risk
        prediction with a Generative AI medical chatbot.

        It helps assess patient risk, explain medical
        conditions, and provide healthcare education
        through an interactive dashboard.
        """
    )

    st.markdown("---")

    st.caption(
        "Built with Streamlit, XGBoost, Groq and GPT-OSS"
    )

# ===================================================
# ICU RISK PREDICTOR
# ===================================================

if page == "📈 ICU Risk Predictor":

    st.markdown(
        """
        <div class="health-card">
        <h3>📈 ICU Risk Prediction</h3>
        Predict ICU admission risk using patient vitals.
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "🤖 Model",
            "XGBoost"
        )

    with c2:
        st.metric(
            "🏥 Use Case",
            "ICU Triage"
        )

    with c3:
        st.metric(
            "📊 Result",
            "Risk Score"
        )

    st.markdown("---")

    if "clf" in st.session_state:

        streamlit_predict_custom_input(
            st.session_state.clf
        )

# ===================================================
# MEDICAL CHATBOT
# ===================================================

elif page == "🤖 Medical AI Chatbot":

    c1, c2 = st.columns([5, 1])

    with c1:

        st.markdown(
            """
            <div class="chat-header">
            🤖 Medical AI Assistant
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        if st.button(
            "🧹 Clear Chat",
            use_container_width=True
        ):
            st.session_state.messages = []
            st.rerun()

    st.markdown(
        """
        <div class="medical-warning">
        ⚠️ Educational information only.
        Consult qualified healthcare professionals
        for diagnosis or treatment decisions.
        </div>
        """,
        unsafe_allow_html=True
    )

    if len(st.session_state.messages) == 0:

        st.info(
            """
            Suggested Questions

            • What are symptoms of diabetes?

            • Explain hypertension.

            • Causes of chest pain?

            • How can I improve heart health?

            • What does high blood pressure mean?

            • Explain my symptoms in simple language.
            """
        )

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input(
        "Ask a medical question..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner(
                "🩺 Analyzing your question..."
            ):

                response = get_medical_response(
                    prompt
                )

                st.markdown(response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )

# ===================================================
# ABOUT PAGE
# ===================================================

elif page == "📖 About":

    st.markdown(
        """
        <div class="health-card">
        <h2>📖 About RiskCare</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """

### 🏥 Overview

RiskCare is an AI-powered healthcare assistant that combines
machine learning and Generative AI to support healthcare
education and ICU risk assessment.

---

### 📈 ICU Risk Prediction

Uses an XGBoost model trained on patient vital signs to
estimate the likelihood of ICU admission.

Input Features:

- Heart Rate
- Blood Pressure
- Temperature
- Respiratory Rate
- Comorbidity Index

Output:

- ICU Risk Probability (%)
- Risk Classification
- Explanation of Risk Factors

---

### 🤖 Medical AI Assistant

Powered by:

- Groq API
- GPT-OSS (open-weight LLM)
- Streamlit Chat Interface

Capabilities:

- Symptom explanations
- Disease information
- Medical terminology assistance
- Preventive healthcare guidance
- Health education

---

### 🛠 Tech Stack

- Python
- XGBoost
- Streamlit
- Groq API
- GPT-OSS (open-weight LLM)
- Joblib

---

### ⚠ Disclaimer

This application is intended for educational
and demonstration purposes only.

It is not designed to diagnose,
treat, prescribe, or replace
professional medical consultation.

        """
    )
