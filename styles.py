"""
styles.py — visual theme for the RiskCare app.

Design rule: every custom element sets BOTH its background and its text color,
so nothing depends on the browser's light/dark preference. The base theme is
locked in .streamlit/config.toml (light, teal accent); these styles match it.

Palette
  primary   #0e7490  (teal-700)     accents, buttons, active nav
  primary-dk #155e75 (teal-800)     hover
  ink       #0f172a  (slate-900)    headings / body text
  muted     #475569  (slate-600)    secondary text
  line      #cbd5e1  (slate-300)    borders
  card      #ffffff                 cards, metrics, form
  page      #f4f8fb                 background
"""


def load_css():
    return """
    <style>
    /* ---------------------------
       Streamlit chrome
    --------------------------- */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    /* keep the header: it holds the sidebar toggle */
    header[data-testid="stHeader"] { background: rgba(244,248,251,0.85); }

    /* ---------------------------
       Page
    --------------------------- */
    .stApp {
        background: linear-gradient(160deg, #f7fafc 0%, #eef5fa 100%);
        color: #0f172a;
    }
    .block-container { padding-top: 1.5rem; }

    /* ---------------------------
       Title
    --------------------------- */
    .main-title {
        text-align: center;
        font-size: 40px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    .subtitle {
        text-align: center;
        color: #475569;
        font-size: 17px;
        margin-bottom: 18px;
    }

    /* ---------------------------
       Cards (custom HTML blocks)
    --------------------------- */
    .health-card {
        background: #ffffff;
        color: #0f172a;
        padding: 20px 24px;
        border-radius: 16px;
        border: 1px solid #cbd5e1;
        border-left: 6px solid #0e7490;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
        margin-bottom: 16px;
    }
    .health-card h2, .health-card h3 {
        color: #0f172a;
        margin: 0 0 6px 0;
    }
    .health-card p { color: #475569; margin: 0; }

    /* ---------------------------
       Sidebar
    --------------------------- */
    section[data-testid="stSidebar"] {
        background: #e6eef5;
        border-right: 1px solid #cbd5e1;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li { color: #0f172a; }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #475569; }
    section[data-testid="stSidebar"] hr { border-color: #cbd5e1; }

    /* ---------------------------
       Top navigation (horizontal radio styled as pills)
    --------------------------- */
    div[role="radiogroup"] {
        display: flex;
        gap: 10px;
        padding: 8px;
        border-radius: 14px;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        margin-bottom: 18px;
    }
    div[role="radiogroup"] label {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 6px 14px;
        margin: 0;
        cursor: pointer;
        transition: background .15s, color .15s;
    }
    div[role="radiogroup"] label p,
    div[role="radiogroup"] label div,
    div[role="radiogroup"] label span { color: #0f172a; font-weight: 600; }
    /* hide the round radio indicator so the labels read as tabs */
    div[role="radiogroup"] label > div:first-child { display: none; }
    div[role="radiogroup"] label:hover { background: #e0f2fe; border-color: #0e7490; }
    /* active pill: teal background, white text */
    div[role="radiogroup"] label:has(input:checked) {
        background: #0e7490;
        border-color: #0e7490;
    }
    div[role="radiogroup"] label:has(input:checked) p,
    div[role="radiogroup"] label:has(input:checked) div,
    div[role="radiogroup"] label:has(input:checked) span { color: #ffffff; }

    /* ---------------------------
       Metrics
    --------------------------- */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] p { color: #475569; font-weight: 600; }
    [data-testid="stMetricValue"]   { color: #0e7490; font-weight: 700; }

    /* ---------------------------
       Form + inputs
    --------------------------- */
    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        padding: 20px 24px;
    }
    label[data-testid="stWidgetLabel"] p,
    .stNumberInput label p, .stSlider label p { color: #0f172a; font-weight: 600; }
    .stNumberInput input {
        background: #ffffff;
        color: #0f172a;
        border-radius: 8px;
    }
    .stNumberInput [data-baseweb="input"] { border-color: #cbd5e1; }
    .stNumberInput button { color: #0f172a; }
    h2, h3, .stSubheader { color: #0f172a; }

    /* ---------------------------
       Buttons
    --------------------------- */
    .stButton button, [data-testid="stFormSubmitButton"] button {
        background: #0e7490;
        color: #ffffff;
        border: 1px solid #0e7490;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.55rem 1.1rem;
    }
    .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
        background: #155e75;
        border-color: #155e75;
        color: #ffffff;
    }
    .stButton button p, [data-testid="stFormSubmitButton"] button p { color: #ffffff; }

    /* ---------------------------
       Chat
    --------------------------- */
    .chat-header {
        text-align: left;
        font-size: 30px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .medical-warning {
        background: #fff7ed;
        color: #7c2d12;
        border: 1px solid #fed7aa;
        border-left: 6px solid #ea580c;
        padding: 14px 16px;
        border-radius: 12px;
        margin-bottom: 18px;
        font-weight: 500;
    }
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 8px;
        color: #0f172a;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { color: #0f172a; }
    [data-testid="stChatInput"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 14px;
    }
    [data-testid="stChatInput"] textarea { color: #0f172a; }

    /* ---------------------------
       Expander
    --------------------------- */
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
    }
    [data-testid="stExpander"] summary p { color: #0f172a; font-weight: 600; }

    /* ---------------------------
       Alerts (st.info / success / warning / error): readable text
    --------------------------- */
    [data-testid="stAlert"] p, [data-testid="stAlert"] li { color: #0f172a; }
    </style>
    """
