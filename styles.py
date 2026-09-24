"""
styles.py — visual theme for the RiskCare app.

Design rule: every element sets BOTH its background and its text colour, so the
app looks identical whether Streamlit is in light or dark theme and whatever
the visitor's browser preference is. (.streamlit/config.toml additionally locks
the light theme, but these styles do not depend on it.)

Palette
  primary    #0e7490 (teal-700)   accents, buttons
  primary-dk #155e75 (teal-800)   hover
  ink        #0f172a (slate-900)  headings / body text
  muted      #475569 (slate-600)  secondary text
  line       #cbd5e1 (slate-300)  borders
  card       #ffffff              cards, form, chat bubbles
  page       #f4f8fb              background
  risk bands low #16a34a · moderate #d97706 · high #ea580c · critical #dc2626
"""

import re

import streamlit as st


def html(markup):
    """
    Collapses an HTML snippet onto one line. Markdown treats blank or deeply indented lines
    inside HTML as code blocks (which is how stray "</div>" text ends up on the page), so every
    custom HTML block goes through here before being rendered.
    """
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def render_html(markup, **kwargs):
    st.markdown(html(markup), unsafe_allow_html=True, **kwargs)


def load_css():
    return """
    <style>
    /* =========================================================
       0. Base: page, header, bottom bar
       ========================================================= */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header[data-testid="stHeader"] { background: rgba(244,248,251,0.92); }
    header[data-testid="stHeader"] * { color: #0f172a; }

    .stApp {
        background: linear-gradient(160deg, #f7fafc 0%, #eef5fa 100%);
        color: #0f172a;
    }
    .block-container { padding-top: 1.5rem; padding-bottom: 5rem; }

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
        text-align: center; font-size: 38px; font-weight: 800;
        color: #0f172a; margin-bottom: 2px; letter-spacing: -0.5px;
    }
    .subtitle { text-align: center; color: #475569; font-size: 17px; margin-bottom: 22px; }

    /* =========================================================
       3. Intro card + model chips
       ========================================================= */
    .health-card {
        background: #ffffff; color: #0f172a;
        padding: 18px 22px; border-radius: 16px;
        border: 1px solid #cbd5e1; border-left: 6px solid #0e7490;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06); margin-bottom: 12px;
    }
    .health-card * { color: #0f172a; }
    .health-card h3 { margin: 0 0 4px 0; padding: 0; }
    .health-card p { color: #475569 !important; margin: 0; }

    /* model summary: compact key facts, 3 x 2 */
    .model-grid {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
        margin-top: 14px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
        background: #f8fafc;
    }
    .model-grid div {
        padding: 10px 14px; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;
        min-width: 0;
    }
    .model-grid div:nth-child(3n) { border-right: none; }
    .model-grid div:nth-last-child(-n+3) { border-bottom: none; }
    .model-grid .k, .model-grid .v {
        display: block; white-space: nowrap; word-break: keep-all; overflow-wrap: normal;
        overflow: hidden; text-overflow: ellipsis;
    }
    .model-grid .k { font-size: 11px; font-weight: 700; letter-spacing: .05em;
                     text-transform: uppercase; color: #64748b !important; }
    .model-grid .v { font-size: 17px; font-weight: 700; color: #0e7490 !important; margin-top: 2px; }

    /* =========================================================
       4. Sidebar
       ========================================================= */
    section[data-testid="stSidebar"] { background: #e6eef5; border-right: 1px solid #cbd5e1; }
    [data-testid="stSidebarHeader"] { height: 2.5rem; padding-top: 0.5rem; padding-bottom: 0; }
    [data-testid="stSidebarUserContent"] { padding-top: 0.25rem; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li { color: #0f172a; }

    .brand { display: flex; align-items: center; gap: 12px; padding: 4px 2px 18px 2px;
             border-bottom: 1px solid #cbd5e1; margin-bottom: 16px; }
    .brand-logo {
        width: 46px; height: 46px; border-radius: 12px; background: #0e7490;
        display: flex; align-items: center; justify-content: center; font-size: 24px;
        box-shadow: 0 4px 10px rgba(14, 116, 144, 0.3);
    }
    .brand-name { font-size: 22px; font-weight: 800; color: #0f172a; line-height: 1.1; }
    .brand-tag  { font-size: 13px; color: #475569; margin-top: 2px; }

    .side-card {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px;
        padding: 12px 14px; margin-bottom: 12px;
    }
    .side-title {
        font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
        color: #0e7490; margin-bottom: 8px;
    }
    .step { display: flex; gap: 10px; align-items: flex-start; font-size: 14px; color: #0f172a;
            margin-bottom: 8px; line-height: 1.35; }
    .step:last-child { margin-bottom: 0; }
    .step span {
        flex: 0 0 22px; height: 22px; border-radius: 50%; background: #e0f2fe; color: #0e7490;
        font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center;
    }
    .side-status { font-size: 14px; color: #0f172a; word-break: break-word; }
    .side-disclaimer {
        background: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px;
        padding: 10px 12px; font-size: 12.5px; color: #7c2d12; line-height: 1.4;
    }
    .side-footer { font-size: 12px; color: #64748b; text-align: center; margin-top: 14px; }

    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
    .dot.on  { background: #16a34a; }
    .dot.off { background: #f59e0b; }

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
       6. Form + inputs
       ========================================================= */
    [data-testid="stForm"] {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 18px 22px;
    }
    .form-section {
        font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
        color: #0e7490; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin: 4px 0 6px 0;
    }
    label[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] * { color: #0f172a; font-weight: 600; }
    [data-baseweb="input"], [data-baseweb="base-input"] {
        background: #ffffff !important; border-color: #cbd5e1 !important; border-radius: 8px;
    }
    .stNumberInput input, .stTextInput input { background: #ffffff !important; color: #0f172a !important; }
    .stNumberInput button { background: #f1f5f9 !important; color: #0f172a !important; border-color: #cbd5e1 !important; }
    [data-baseweb="select"] > div { background: #ffffff !important; border-color: #cbd5e1 !important; }
    [data-baseweb="select"] * { color: #0f172a; }
    [data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stTickBarMin"],
    [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: #0f172a; }
    [data-testid="stSlider"] div[role="slider"] { background: #0e7490 !important; }
    [data-testid="stCheckbox"] p, .stToggle p { color: #0f172a; }

    /* =========================================================
       7. Buttons
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
       8. Risk result
       ========================================================= */
    .section-title { font-size: 22px; font-weight: 700; color: #0f172a; margin: 18px 0 10px 0; }
    .sub-title { font-size: 16px; font-weight: 700; color: #0f172a; margin: 6px 0 10px 0; }

    .result-grid { display: grid; grid-template-columns: 3fr 2fr; gap: 14px; margin-bottom: 14px; }
    @media (max-width: 900px) { .result-grid { grid-template-columns: 1fr; } }

    .result-card {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 16px 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }
    .result-card.band-low      { border-top: 5px solid #16a34a; }
    .result-card.band-moderate { border-top: 5px solid #d97706; }
    .result-card.band-high     { border-top: 5px solid #ea580c; }
    .result-card.band-critical { border-top: 5px solid #dc2626; }
    .result-card.news-card     { border-top: 5px solid #64748b; }

    .result-label { font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: #475569; }
    .result-main  { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 4px 0 10px 0; }
    .result-prob  { font-size: 44px; font-weight: 800; color: #0f172a; line-height: 1.1; }

    .band-pill { font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }
    .band-pill.band-low,      .band-pill.news-low        { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .band-pill.band-moderate, .band-pill.news-lowmedium  { background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
    .band-pill.band-high,     .band-pill.news-medium     { background: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }
    .band-pill.band-critical, .band-pill.news-high       { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

    .gauge { height: 10px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
    .gauge-fill { height: 100%; border-radius: 999px; }
    .gauge-fill.band-low      { background: #16a34a; }
    .gauge-fill.band-moderate { background: #d97706; }
    .gauge-fill.band-high     { background: #ea580c; }
    .gauge-fill.band-critical { background: #dc2626; }
    .gauge-scale { display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-top: 4px; }

    .news-note  { font-size: 13px; color: #475569; line-height: 1.45; }
    .news-flags { font-size: 13px; color: #b91c1c; font-weight: 600; margin-top: 6px; }
    .news-scale { display: flex; gap: 4px; margin: 2px 0 8px 0; }
    .news-scale span {
        flex: 1; text-align: center; font-size: 11px; font-weight: 600; padding: 3px 0; border-radius: 6px;
        color: #475569; background: #f1f5f9; border: 1px solid transparent;
    }
    .news-scale span.on.low    { background: #dcfce7; color: #15803d; border-color: #86efac; }
    .news-scale span.on.medium { background: #ffedd5; color: #c2410c; border-color: #fdba74; }
    .news-scale span.on.high   { background: #fee2e2; color: #b91c1c; border-color: #fca5a5; }

    /* analysis progress shown while a prediction runs */
    [data-testid="stExpander"]:has([data-testid="stStatusWidget"]),
    [data-testid="stStatusWidget"] { border-radius: 12px; }
    .analysis-step { font-size: 14px; color: #0f172a; margin: 2px 0; }
    .analysis-step .tick { color: #16a34a; font-weight: 700; margin-right: 6px; }

    /* multiple patients: ward overview tiles */
    .ward-tiles { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; margin: 4px 0 6px 0; }
    .ward-tile {
        background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 12px;
        border-top: 4px solid #64748b; min-width: 0;
    }
    .ward-tile .n { display: block; font-size: 26px; font-weight: 800; color: #0f172a; line-height: 1.1; }
    .ward-tile .l { display: block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
                    text-transform: uppercase; color: #475569; white-space: nowrap;
                    overflow: hidden; text-overflow: ellipsis; }
    .ward-tile.total         { border-top-color: #0e7490; }
    .ward-tile.band-low      { border-top-color: #16a34a; }
    .ward-tile.band-moderate { border-top-color: #d97706; }
    .ward-tile.band-high     { border-top-color: #ea580c; }
    .ward-tile.band-critical { border-top-color: #dc2626; }
    .ward-note { font-size: 13px; color: #475569; margin-bottom: 8px; }
    @media (max-width: 900px) { .ward-tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); } }


    /* =========================================================
       9. Assistant panel (right column, stays in view while the page scrolls)
       ========================================================= */
    [data-testid="stColumn"]:has(.st-key-chat_panel) {
        position: sticky; top: 3.75rem; align-self: flex-start;
        min-width: min(270px, 100%);   /* room for the name and all three header buttons */
    }
    .st-key-chat_panel {
        background: #ffffff; border: 1px solid #cbd5e1; border-top: 5px solid #0e7490;
        border-radius: 18px; padding: 14px 16px 10px 16px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.10);
    }

    .chat-header { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 2px 0; }
    .chat-header > div:last-child { min-width: 0; }
    .chat-avatar {
        flex: 0 0 38px; height: 38px; border-radius: 50%; background: #e0f2fe;
        display: flex; align-items: center; justify-content: center; font-size: 20px;
    }
    .chat-title  { font-size: 18px; font-weight: 700; color: #0f172a; line-height: 24px; white-space: nowrap;
                   overflow: hidden; text-overflow: ellipsis; }
    .chat-status { font-size: 13px; color: #475569; line-height: 18px; white-space: nowrap;
                   overflow: hidden; text-overflow: ellipsis; }

    /* header actions: round icon-only buttons (tooltips carry the label) */
    /* header row never wraps; it is tall enough for title + status, and the title keeps
       enough room to stay readable while the three buttons keep their size */
    .st-key-chat_head { gap: 2px; flex-wrap: nowrap !important; min-height: 48px; overflow: visible;
                        container-type: inline-size; }
    .st-key-chat_head > div { flex-shrink: 0; overflow: visible; }
    .st-key-chat_head > div:has(.chat-header) { flex: 1 1 auto !important; min-width: 118px !important; }
    .st-key-chat_head [data-testid="stMarkdownContainer"],
    .st-key-chat_head [data-testid="stMarkdown"] { min-width: 0; overflow: visible; }
    .st-key-chat_head [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
    /* very narrow panel: drop the avatar so the name stays fully visible */
    @container (max-width: 250px) { .chat-avatar { display: none; } }
    .st-key-clear_chat button, .st-key-close_chat button, .st-key-resize_chat button {
        width: 34px; height: 34px; min-height: 34px; padding: 0 !important;
        border-radius: 50% !important; background: transparent !important; border: none !important;
        display: flex; align-items: center; justify-content: center;
    }
    .st-key-clear_chat button *, .st-key-close_chat button *, .st-key-resize_chat button * {
        color: #64748b !important; font-size: 20px;
    }
    .st-key-clear_chat button:hover, .st-key-close_chat button:hover, .st-key-resize_chat button:hover {
        background: #f1f5f9 !important;
    }
    .st-key-clear_chat button:hover *, .st-key-close_chat button:hover *,
    .st-key-resize_chat button:hover * { color: #0e7490 !important; }

    /* full-page chat: predictor stays mounted (keeps its inputs) but is hidden */
    .st-key-predictor_hidden { display: none !important; }
    .st-key-chat_panel_full {
        background: #ffffff; border: 1px solid #cbd5e1; border-top: 5px solid #0e7490;
        border-radius: 18px; padding: 16px 22px 12px 22px; max-width: 1100px; margin: 0 auto;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.10);
    }
    .st-key-chat_panel_full [data-testid="stChatMessage"] { padding: 12px 18px; }
    [data-testid="stChatMessage"] table { font-size: 14px; }

    /* suggestion chips: light outline instead of solid teal */
    .st-key-chat_box .stButton button {
        background: #f8fafc; border: 1px solid #cbd5e1; padding: 0.3rem 0.7rem; border-radius: 10px;
        min-height: 0;
    }
    .st-key-chat_box .stButton button * { color: #334155; font-weight: 500; font-size: 13.5px; }
    .st-key-chat_box .stButton button:hover { background: #e0f2fe; border-color: #0e7490; }
    .st-key-chat_box .stButton button { justify-content: flex-start; text-align: left; }

    .setup-card {
        background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px;
        padding: 12px 14px; margin: 6px 0 8px 0; font-size: 13.5px; color: #0f172a; line-height: 1.45;
    }
    .setup-card a { color: #0e7490; font-weight: 600; }
    .setup-title { font-weight: 700; font-size: 15px; margin-bottom: 4px; }

    .patient-context {
        background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 12px;
        padding: 10px 12px; margin: 4px 0 10px 0; font-size: 13px; color: #0f172a;
    }
    .patient-context.general { background: #f8fafc; border-color: #cbd5e1; color: #475569; }
    .patient-context b { color: #0f172a; }
    .pc-title { font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .pc-vitals { color: #475569; line-height: 1.5; }
    .pc-ward { color: #0e7490; font-weight: 600; margin-top: 4px; }

    /* headings inside chat replies stay in proportion with the text */
    .st-key-chat_box h1, .st-key-chat_box h2 { font-size: 20px !important; padding: 10px 0 4px 0 !important; }
    .st-key-chat_box h3 { font-size: 17px !important; padding: 10px 0 4px 0 !important; }
    .st-key-chat_box h4 { font-size: 15px !important; }

    /* secondary action under the report card */
    .st-key-use_report_vitals button {
        background: #ffffff !important; color: #1d4ed8 !important; border: 1px solid #93c5fd !important;
        box-shadow: none !important; min-height: 36px;
    }
    .st-key-use_report_vitals button:hover { background: #eff6ff !important; }
    .st-key-use_report_vitals button p, .st-key-use_report_vitals button span { color: #1d4ed8 !important; }

    /* medical reports */
    .report-card {
        background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px;
        padding: 10px 12px; margin: 0 0 10px 0; font-size: 13px; color: #0f172a;
    }
    .rc-title { font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
                color: #1d4ed8; margin-bottom: 4px; }
    .rc-item { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; line-height: 1.5; }
    .rc-item b { color: #0f172a; overflow-wrap: anywhere; }
    .rc-item span { color: #475569; }
    .rc-item span::before { content: "·"; margin-right: 6px; }
    .upload-hint {
        display: flex; gap: 10px; align-items: flex-start; background: #ffffff;
        border: 1px dashed #93c5fd; border-radius: 12px; padding: 10px 12px; margin: 4px 0 10px 0;
        font-size: 13px; color: #475569; line-height: 1.45;
    }
    .upload-hint > span { font-size: 18px; line-height: 1.2; }
    .upload-hint b { color: #0f172a; }
    .file-chip {
        display: inline-flex; align-items: center; gap: 6px; max-width: 100%;
        background: #eff6ff; border: 1px solid #bfdbfe; color: #1e3a8a; border-radius: 8px;
        padding: 4px 10px; margin: 0 6px 6px 0; font-size: 13px; font-weight: 600; overflow-wrap: anywhere;
    }

    .st-key-chat_box { background: #f8fafc; border: 1px solid #e2e8f0 !important; border-radius: 14px; }

    .chat-disclaimer { font-size: 11.5px; color: #7c2d12; text-align: center; margin-top: 4px; }

    [data-testid="stChatMessage"] {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 10px 14px; margin-bottom: 8px;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: #e0f2fe; border-color: #bae6fd;
    }
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

    /* floating launcher shown while the panel is hidden */
    .st-key-open_chat { position: fixed; right: 28px; bottom: 28px; z-index: 1000; width: auto !important; }
    .st-key-open_chat button {
        border-radius: 999px !important; padding: 0.75rem 1.3rem !important;
        box-shadow: 0 10px 24px rgba(14, 116, 144, 0.35);
    }

    /* =========================================================
       10. Expander, dataframe & spinner
       ========================================================= */
    [data-testid="stExpander"] { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; }
    [data-testid="stExpander"] summary * { color: #0f172a; font-weight: 600; }
    [data-testid="stSpinner"] p { color: #0f172a; }
    </style>
    """


_TAG_EXCEPT_BR = re.compile(r"<(?!br\s*/?>)", re.IGNORECASE)


def render_message(text):
    """
    Renders a chatbot reply. Models often put <br> inside Markdown table cells for line breaks;
    those are rendered as real line breaks, while any other HTML is shown as plain text
    (outside code blocks), so model output can never inject markup into the page.
    """
    parts = text.split("```")
    for i in range(0, len(parts), 2):          # even parts are outside ``` code fences
        parts[i] = _TAG_EXCEPT_BR.sub("&lt;", parts[i])
    st.markdown("```".join(parts), unsafe_allow_html=True)
