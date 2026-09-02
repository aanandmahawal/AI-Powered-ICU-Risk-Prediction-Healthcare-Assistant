"""
styles.py — visual theme for the RiskCare app.

Design rule: every element sets BOTH its background and its text colour, so the
app looks identical whether Streamlit is in light or dark theme and whatever
the visitor's browser preference is. (.streamlit/config.toml additionally locks
the light theme, but these styles do not depend on it.)

Palette
  primary    #0e7490 (teal-700)   accents, buttons, active nav
  primary-dk #155e75 (teal-800)   hover
  ink        #0f172a (slate-900)  headings / body text
  muted      #475569 (slate-600)  secondary text
  line       #cbd5e1 (slate-300)  borders
  card       #ffffff              cards, metrics, form, chat bubbles
  page       #f4f8fb              background
"""


def load_css():
    return """
    <style>
    /* =========================================================
       0. Base: page, header, bottom bar (chat input area)
       ========================================================= */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header[data-testid="stHeader"] { background: rgba(244,248,251,0.92); }
    header[data-testid="stHeader"] * { color: #0f172a; }

    .stApp {
        background: linear-gradient(160deg, #f7fafc 0%, #eef5fa 100%);
        color: #0f172a;
    }
    .block-container { padding-top: 1.5rem; }

    /* the fixed band that holds st.chat_input takes the theme background -> force ours */
    [data-testid="stBottom"], [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        background: #eef5fa !important;
    }

    /* =========================================================
       1. Text colours everywhere (theme-proof)
       ========================================================= */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 { color: #0f172a; }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] strong, [data-testid="stMarkdownContainer"] em,
    [data-testid="stMarkdownContainer"] td, [data-testid="stMarkdownContainer"] th,
    [data-testid="stMarkdownContainer"] blockquote { color: #0f172a; }
    [data-testid="stMarkdownContainer"] a { color: #0e7490; }
    [data-testid="stCaptionContainer"] p, .stCaption { color: #475569; }
    hr { border-color: #cbd5e1; }

    /* tables produced by markdown (e.g. chatbot answers) */
    [data-testid="stMarkdownContainer"] table {
        border-collapse: collapse; width: 100%; margin: 8px 0 12px 0;
        background: #ffffff;
    }
    [data-testid="stMarkdownContainer"] th {
        background: #e6eef5; font-weight: 700; text-align: left;
    }
    [data-testid="stMarkdownContainer"] th, [data-testid="stMarkdownContainer"] td {
        border: 1px solid #cbd5e1; padding: 6px 10px;
    }
    [data-testid="stMarkdownContainer"] blockquote {
        border-left: 4px solid #0e7490; background: #f1f5f9; padding: 6px 12px; margin: 8px 0;
    }
    /* inline code and code blocks */
    [data-testid="stMarkdownContainer"] code {
        background: #eef2f7; color: #0f172a; border-radius: 4px; padding: 1px 5px;
    }
    [data-testid="stMarkdownContainer"] pre,
    [data-testid="stMarkdownContainer"] pre code {
        background: #eef2f7; color: #0f172a;
    }

    /* =========================================================
       2. Title
       ========================================================= */
    .main-title {
        text-align: center; font-size: 40px; font-weight: 800;
        color: #0f172a; margin-bottom: 4px; letter-spacing: -0.5px;
    }
    .subtitle { text-align: center; color: #475569; font-size: 17px; margin-bottom: 18px; }

    /* =========================================================
       3. Cards (custom HTML blocks)
       ========================================================= */
    .health-card {
        background: #ffffff; color: #0f172a;
        padding: 20px 24px; border-radius: 16px;
        border: 1px solid #cbd5e1; border-left: 6px solid #0e7490;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06); margin-bottom: 16px;
    }
    .health-card * { color: #0f172a; }
    .health-card h2, .health-card h3 { margin: 0 0 6px 0; }
    .health-card p { color: #475569; margin: 0; }

    /* =========================================================
       4. Sidebar
       ========================================================= */
    section[data-testid="stSidebar"] { background: #e6eef5; border-right: 1px solid #cbd5e1; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li { color: #0f172a; }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #475569; }

    /* =========================================================
       5. Alerts (st.info / success / warning / error): light look always
       ========================================================= */
    [data-testid="stAlertContainer"] { border-radius: 12px; border: 1px solid transparent; }
    [data-testid="stAlertContainer"] * { color: #0f172a; }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"])    { background: #dbeafe; border-color: #93c5fd; }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) { background: #dcfce7; border-color: #86efac; }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background: #fef3c7; border-color: #fcd34d; }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"])   { background: #fee2e2; border-color: #fca5a5; }

    /* =========================================================
       6. Top navigation (horizontal radio styled as tabs)
       ========================================================= */
    div[role="radiogroup"] {
        display: flex; gap: 10px; padding: 8px; border-radius: 14px;
        background: #ffffff; border: 1px solid #cbd5e1; margin-bottom: 18px;
    }
    div[role="radiogroup"] label {
        background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px;
        padding: 6px 14px; margin: 0; cursor: pointer; transition: background .15s, color .15s;
    }
    div[role="radiogroup"] label * { color: #0f172a; font-weight: 600; }
    /* hide the round radio indicator (the element before the label text) */
    div[role="radiogroup"] label > div > div > div:first-child:not([data-testid]) { display: none; }
    div[role="radiogroup"] label:hover { background: #e0f2fe; border-color: #0e7490; }
    /* active tab (Streamlit sets data-selected on the label; :has() is a fallback) */
    div[role="radiogroup"] label[data-selected="true"],
    div[role="radiogroup"] label:has(input:checked) { background: #0e7490; border-color: #0e7490; }
    div[role="radiogroup"] label[data-selected="true"] *,
    div[role="radiogroup"] label:has(input:checked) * { color: #ffffff; }

    /* =========================================================
       7. Metrics
       ========================================================= */
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 14px; padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] p { color: #475569; font-weight: 600; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #0e7490 !important; font-weight: 700; }

    /* =========================================================
       8. Form + inputs
       ========================================================= */
    [data-testid="stForm"] {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 20px 24px;
    }
    label[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] * { color: #0f172a; font-weight: 600; }
    [data-baseweb="input"], [data-baseweb="base-input"] {
        background: #ffffff !important; border-color: #cbd5e1 !important; border-radius: 8px;
    }
    .stNumberInput input, .stTextInput input { background: #ffffff !important; color: #0f172a !important; }
    .stNumberInput button { background: #f1f5f9 !important; color: #0f172a !important; border-color: #cbd5e1 !important; }
    [data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stTickBarMin"],
    [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: #0f172a; }
    [data-testid="stSlider"] div[role="slider"] { background: #0e7490 !important; }

    /* =========================================================
       9. Buttons
       ========================================================= */
    .stButton button, [data-testid="stFormSubmitButton"] button {
        background: #0e7490; border: 1px solid #0e7490; border-radius: 12px;
        font-weight: 600; padding: 0.55rem 1.1rem;
    }
    .stButton button *, [data-testid="stFormSubmitButton"] button * { color: #ffffff; }
    .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
        background: #155e75; border-color: #155e75;
    }

    /* =========================================================
       10. Chat
       ========================================================= */
    .chat-header { text-align: left; font-size: 30px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
    .medical-warning {
        background: #fff7ed; border: 1px solid #fed7aa; border-left: 6px solid #ea580c;
        padding: 14px 16px; border-radius: 12px; margin-bottom: 18px; font-weight: 500;
    }
    .medical-warning, .medical-warning * { color: #7c2d12; }

    [data-testid="stChatMessage"] {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 14px;
        padding: 10px 14px; margin-bottom: 8px;
    }
    /* everything inside a chat bubble is dark text (headings, tables, bold, quotes...) */
    [data-testid="stChatMessage"] *:not(code):not(pre) { color: #0f172a; }
    [data-testid="stChatMessage"] a { color: #0e7490; }

    [data-testid="stChatInput"], [data-testid="stChatInput"] > div {
        background: #ffffff !important; border-radius: 14px;
    }
    [data-testid="stChatInput"] > div { border: 1px solid #cbd5e1 !important; }
    [data-testid="stChatInput"] > div:focus-within { border-color: #0e7490 !important; box-shadow: 0 0 0 1px #0e7490; }
    [data-testid="stChatInput"] textarea { color: #0f172a !important; background: #ffffff !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: #64748b; }
    [data-testid="stChatInputSubmitButton"] { background: #0e7490 !important; border-radius: 10px; color: #ffffff !important; }
    [data-testid="stChatInputSubmitButton"] svg { color: #ffffff; }

    /* =========================================================
       11. Expander & spinner
       ========================================================= */
    [data-testid="stExpander"] { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; }
    [data-testid="stExpander"] summary * { color: #0f172a; font-weight: 600; }
    [data-testid="stSpinner"] p { color: #0f172a; }
    </style>
    """
