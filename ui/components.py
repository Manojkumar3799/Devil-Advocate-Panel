"""UI components and visual styling primitives for Devil's Advocate Panel."""

from __future__ import annotations

import streamlit as st

# Color token definitions strictly following UI Design Brief §1
THEME_TOKENS = {
    "dark": {
        "bg_primary": "#12141A",
        "bg_surface": "#1B1E26",
        "bg_elevated": "#242833",
        "border_hairline": "#343A47",
        "text_primary": "#E8E6DF",
        "text_secondary": "#8D93A3",
        "accent": "#C6A15B",
        "accent_hover": "#D9B876",
        "severity_low": "#5C8A6E",
        "severity_medium": "#C6A15B",
        "severity_high": "#B5623E",
        "severity_critical": "#8A3232",
        "overlay_shadow": "0 4px 24px rgba(0, 0, 0, 0.24)",
        "accent_active_bg": "rgba(198, 161, 91, 0.15)",
    },
    "light": {
        "bg_primary": "#F1F0EC",
        "bg_surface": "#FFFFFF",
        "bg_elevated": "#F7F6F2",
        "border_hairline": "#DEDBD2",
        "text_primary": "#1D1F26",
        "text_secondary": "#6B6F7A",
        "accent": "#A8823E",
        "accent_hover": "#8F6E32",
        "severity_low": "#3F7A56",
        "severity_medium": "#A8823E",
        "severity_high": "#A14A2E",
        "severity_critical": "#7A2727",
        "overlay_shadow": "0 4px 24px rgba(0, 0, 0, 0.08)",
        "accent_active_bg": "rgba(168, 130, 62, 0.15)",
    },
}


def build_css(theme: str) -> str:
    tokens = THEME_TOKENS.get(theme, THEME_TOKENS["dark"])
    # Determine text color on top of accent button (always dark text for contrast in both themes)
    btn_text_color = "#12141A" if theme == "dark" else "#1D1F26"

    return f"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
    --bg-primary: {tokens['bg_primary']};
    --bg-surface: {tokens['bg_surface']};
    --bg-elevated: {tokens['bg_elevated']};
    --border-hairline: {tokens['border_hairline']};
    --text-primary: {tokens['text_primary']};
    --text-secondary: {tokens['text_secondary']};
    --accent: {tokens['accent']};
    --accent-hover: {tokens['accent_hover']};
    --severity-low: {tokens['severity_low']};
    --severity-medium: {tokens['severity_medium']};
    --severity-high: {tokens['severity_high']};
    --severity-critical: {tokens['severity_critical']};
    --overlay-shadow: {tokens['overlay_shadow']};
    --accent-active-bg: {tokens['accent_active_bg']};
    --btn-text-color: {btn_text_color};
}}

/* Motion 1: Theme cross-fade */
body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {{
    transition: background-color 200ms ease, color 200ms ease;
}}

/* Base Typography and Background */
html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-primary);
}}

[data-testid="stAppViewContainer"] {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
}}

[data-testid="stHeader"] {{
    background-color: transparent;
}}

/* Global shell main content area: max-width 840px, centered, generous 48px top padding */
[data-testid="stMainBlockContainer"] {{
    max-width: 840px !important;
    padding-top: 48px !important;
    padding-left: 24px !important;
    padding-right: 24px !important;
    margin: 0 auto !important;
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{
    background-color: var(--bg-surface);
    border-right: 1px solid var(--border-hairline);
}}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
    padding: 24px 16px;
    background-color: var(--bg-surface);
}}

/* Wordmark */
.app-wordmark {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 22px;
    font-weight: 600;
    line-height: 1.2;
    color: var(--text-primary);
    margin-bottom: 24px;
    padding-left: 8px;
}}

/* Sidebar navigation buttons */
.stSidebar button[kind="secondary"],
.stSidebar button[kind="primary"] {{
    border-radius: 999px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 16px !important;
    margin-bottom: 4px !important;
    width: 100% !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
}}

/* Inactive nav button */
.stSidebar button[kind="secondary"] {{
    background-color: transparent !important;
    color: var(--text-secondary) !important;
}}
.stSidebar button[kind="secondary"]:hover {{
    color: var(--text-primary) !important;
    background-color: var(--bg-elevated) !important;
}}

/* Active nav button: 999px pill background in --accent at 15% opacity with --accent text */
.stSidebar button[kind="primary"] {{
    background-color: var(--accent-active-bg) !important;
    color: var(--accent) !important;
    border: 1px solid transparent !important;
}}
.stSidebar button[kind="primary"]:hover {{
    background-color: var(--accent-active-bg) !important;
    color: var(--accent-hover) !important;
}}

/* Theme toggle button in sidebar */
.theme-toggle-container button {{
    background-color: transparent !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    padding: 6px 12px !important;
}}
.theme-toggle-container button:hover {{
    border-color: var(--accent) !important;
    color: var(--text-primary) !important;
}}

/* Headings scale */
h1, .page-title {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 32px !important;
    font-weight: 600 !important;
    line-height: 1.15 !important;
    color: var(--text-primary) !important;
    margin-bottom: 8px !important;
}}

h2, .section-heading {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    color: var(--text-primary) !important;
    margin-top: 24px !important;
    margin-bottom: 12px !important;
}}

h3 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    color: var(--text-primary) !important;
}}

p, div, span, label {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

/* Paragraphs length constraint: ~75ch */
p, .constrained-text {{
    max-width: 75ch;
    line-height: 1.6;
    color: var(--text-primary);
}}

/* Helper & secondary text */
.helper-text, [data-testid="stMarkdownContainer"] p.helper-text, .text-secondary {{
    color: var(--text-secondary) !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
}}

/* Primary Buttons (outside sidebar): 8px radius, --accent background, dark text */
[data-testid="stMainBlockContainer"] button[kind="primary"] {{
    background-color: var(--accent) !important;
    color: var(--btn-text-color) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    padding: 12px 20px !important;
    box-shadow: none !important;
    transition: border-color 120ms ease, background-color 120ms ease;
}}
[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {{
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    color: var(--btn-text-color) !important;
}}

/* Secondary Buttons (e.g. Connect or Disconnect): 8px radius, transparent bg, 1px border */
[data-testid="stMainBlockContainer"] button[kind="secondary"] {{
    background-color: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    padding: 12px 20px !important;
    box-shadow: none !important;
    transition: border-color 120ms ease, background-color 120ms ease;
}}
[data-testid="stMainBlockContainer"] button[kind="secondary"]:hover {{
    background-color: var(--bg-elevated) !important;
    border-color: var(--accent-hover) !important;
    color: var(--accent-hover) !important;
}}

/* Inputs & Textareas: 8px radius, hairline border, bg-elevated */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    background-color: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    box-shadow: none !important;
    transition: border-color 120ms ease;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--accent) !important;
    outline: none !important;
}}

/* Restyle st.expander per §4 and §6:
   remove default box styling, apply card treatment (4px radius, hairline border, --bg-surface bg) */
[data-testid="stExpander"] {{
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
    margin-bottom: 12px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 14px !important;
    color: var(--text-secondary) !important;
    padding: 8px 12px !important;
}}
[data-testid="stExpander"] summary:hover {{
    color: var(--text-primary) !important;
}}
[data-testid="stExpander"] summary svg {{
    fill: var(--text-secondary) !important;
}}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    padding: 12px !important;
    border-top: 1px solid var(--border-hairline) !important;
    background-color: var(--bg-surface) !important;
}}

/* Card container: 4px radius, 1px solid hairline border, bg-surface, NO shadow */
.custom-card {{
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 12px;
}}

/* Intensity card system */
.intensity-card {{
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: 4px;
    padding: 16px;
    cursor: pointer;
    transition: border-color 120ms ease;
    height: 100%;
}}
.intensity-card.selected {{
    border: 2px solid var(--accent) !important;
}}
.intensity-title {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    font-size: 15px;
    color: var(--text-primary);
    margin-bottom: 6px;
}}
.intensity-desc {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.4;
}}

/* Interrogation Persona Card & Turn Animation (§5: Motion 2) */
.interrogation-card {{
    background-color: var(--bg-surface);
    border: 1px solid var(--border-hairline);
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 16px;
}}

@keyframes personaEntrance {{
    from {{
        opacity: 0;
        transform: translateY(6px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.interrogation-card.latest-turn {{
    animation: personaEntrance 400ms ease-out forwards;
}}

@keyframes scalePulse {{
    0% {{
        transform: scale(0.8);
    }}
    50% {{
        transform: scale(1.05);
    }}
    100% {{
        transform: scale(1);
    }}
}}

.resolved-pulse {{
    animation: scalePulse 300ms ease-out forwards;
    display: inline-block;
}}

/* Avatar circle: 50% radius, bg-elevated, 32px */
.avatar-circle {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--bg-elevated);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    vertical-align: middle;
}}

.persona-name-text {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.3;
    color: var(--text-primary);
    vertical-align: middle;
}}

.round-counter-text {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    float: right;
    line-height: 32px;
}}

/* Question text */
.question-text {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-primary);
    margin-top: 12px;
    margin-bottom: 12px;
    max-width: 75ch;
}}

/* Founder reply box inside interrogation card: bg-elevated, no border */
.founder-reply-box {{
    background-color: var(--bg-elevated);
    border: none;
    border-radius: 4px;
    padding: 12px 16px;
    margin-top: 12px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text-primary);
    max-width: 75ch;
}}

/* Progress bar (§5: Motion 3) */
.progress-track {{
    width: 100%;
    height: 2px;
    background-color: var(--border-hairline);
    margin-top: 6px;
    margin-bottom: 16px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    transition: width 400ms ease-in-out;
}}

/* Severity Pills: 999px radius, white/bg-primary text */
.severity-pill {{
    display: inline-block;
    border-radius: 999px;
    padding: 2px 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    line-height: 1.4;
    color: #FFFFFF;
}}
.severity-pill-1, .severity-pill-2 {{
    background-color: var(--severity-low);
}}
.severity-pill-3 {{
    background-color: var(--severity-medium);
    color: #12141A;
}}
.severity-pill-4 {{
    background-color: var(--severity-high);
}}
.severity-pill-5 {{
    background-color: var(--severity-critical);
}}

/* Data / Numeric text */
.data-mono {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
}}

/* Verdict row */
.verdict-row {{
    border-bottom: 1px solid var(--border-hairline);
    padding: 16px 0;
}}
.verdict-row:last-child {{
    border-bottom: none;
}}

/* Respect prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {{
    *, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"],
    .interrogation-card.latest-turn, .resolved-pulse, .progress-fill {{
        transition: none !important;
        animation: none !important;
    }}
}}
"""


def apply_custom_styles():
    theme = st.session_state.get("theme", "dark")
    css = build_css(theme)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_progress_tracker(persona_status: dict):
    """Renders the 3 progress bars per persona at the top of the Live Interrogation screen."""
    personas = [
        ("vc", "VC", "trending_up", "var(--severity-medium)"),
        ("analyst", "Financial Analyst", "calculate", "var(--severity-low)"),
        ("realist", "Market Realist", "public", "var(--severity-high)"),
    ]

    cols = st.columns(3)
    for i, (key, label, icon, color) in enumerate(personas):
        stat = persona_status.get(key, {"resolved": False, "round": 0})
        rnd = stat.get("round", 0)
        resolved = stat.get("resolved", False)
        # Calculate percentage (0 to 3 rounds, or 100% if resolved)
        pct = 100 if resolved else min(100, int((rnd / 3) * 100))

        with cols[i]:
            status_desc = f":material/check_circle: Resolved" if resolved else f"Round {rnd} of 3"
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; color: var(--text-primary);">
                        :material/{icon}: {label}
                    </span>
                    <span class="data-mono" style="font-size: 13px;">
                        {status_desc}
                    </span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: {pct}%; background-color: {color};"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
