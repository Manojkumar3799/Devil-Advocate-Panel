"""UI components and visual styling primitives for Devil's Advocate Panel.

Cinematic 'The Hot Seat' theme with glassmorphism, glow accents, ambient embers,
and optimized font loading.
"""

from __future__ import annotations

import streamlit as st

# Color token definitions strictly following UI Design Brief & The Hot Seat Spec
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
        "overlay_shadow": "0 8px 32px rgba(0, 0, 0, 0.35)",
        "accent_active_bg": "rgba(198, 161, 91, 0.15)",
        "glass_bg": "rgba(27, 30, 38, 0.55)",
        "glass_border": "rgba(198, 161, 91, 0.18)",
        "glass_shadow": "0 8px 32px rgba(0, 0, 0, 0.35)",
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
        "overlay_shadow": "0 8px 32px rgba(0, 0, 0, 0.08)",
        "accent_active_bg": "rgba(168, 130, 62, 0.15)",
        "glass_bg": "rgba(255, 255, 255, 0.65)",
        "glass_border": "rgba(168, 130, 62, 0.25)",
        "glass_shadow": "0 8px 32px rgba(0, 0, 0, 0.08)",
    },
}


def build_css(theme: str) -> str:
    tokens = THEME_TOKENS.get(theme, THEME_TOKENS["dark"])
    btn_text_color = "#12141A" if theme == "dark" else "#1D1F26"

    return f"""
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
    --glass-bg: {tokens['glass_bg']};
    --glass-border: {tokens['glass_border']};
    --glass-shadow: {tokens['glass_shadow']};
}}

/* Motion: Theme cross-fade */
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
    position: relative;
    z-index: 1;
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
    position: relative;
    z-index: 1;
}}

/* Screen navigation cross-fade + upward slide */
@keyframes screenEntrance {{
    0% {{
        opacity: 0;
        transform: translateY(8px);
    }}
    100% {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.screen-transition-container {{
    animation: screenEntrance 300ms ease-out forwards;
    position: relative;
    z-index: 1;
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{
    background-color: var(--bg-surface);
    border-right: 1px solid var(--border-hairline);
    position: relative;
    z-index: 1;
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
    transition: all 200ms ease !important;
}}

/* Inactive nav button */
.stSidebar button[kind="secondary"] {{
    background-color: transparent !important;
    color: var(--text-secondary) !important;
}}
.stSidebar button[kind="secondary"]:hover {{
    color: var(--text-primary) !important;
    background-color: var(--bg-elevated) !important;
    box-shadow: 0 0 14px rgba(198, 161, 91, 0.2) !important;
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
    box-shadow: 0 0 16px rgba(198, 161, 91, 0.3) !important;
}}

/* Theme toggle button in sidebar */
.theme-toggle-container button {{
    background-color: transparent !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    padding: 6px 12px !important;
    transition: all 200ms ease !important;
}}
.theme-toggle-container button:hover {{
    border-color: var(--accent) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 12px rgba(198, 161, 91, 0.25) !important;
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

/* Primary Buttons with Glow expansion on hover */
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
    transition: all 200ms ease !important;
}}
[data-testid="stMainBlockContainer"] button[kind="primary"]:hover {{
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    color: var(--btn-text-color) !important;
    box-shadow: 0 0 20px rgba(198, 161, 91, 0.5) !important;
}}

/* Secondary Buttons with Glow expansion on hover */
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
    transition: all 200ms ease !important;
}}
[data-testid="stMainBlockContainer"] button[kind="secondary"]:hover {{
    background-color: var(--bg-elevated) !important;
    border-color: var(--accent-hover) !important;
    color: var(--accent-hover) !important;
    box-shadow: 0 0 16px rgba(198, 161, 91, 0.35) !important;
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
    transition: border-color 150ms ease, box-shadow 150ms ease !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--accent) !important;
    outline: none !important;
    box-shadow: 0 0 14px rgba(198, 161, 91, 0.25) !important;
}}

/* Restyle st.expander with glassmorphic panel styling */
[data-testid="stExpander"] {{
    background: var(--glass-bg) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    box-shadow: var(--glass-shadow) !important;
    margin-bottom: 12px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 14px !important;
    color: var(--text-secondary) !important;
    padding: 10px 14px !important;
}}
[data-testid="stExpander"] summary:hover {{
    color: var(--text-primary) !important;
}}
[data-testid="stExpander"] summary svg {{
    fill: var(--text-secondary) !important;
}}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    padding: 14px !important;
    border-top: 1px solid var(--glass-border) !important;
    background: transparent !important;
}}

/* Glassmorphic Panel Cards (The Hot Seat Spec §1) */
.panel-card, .custom-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    box-shadow: var(--glass-shadow);
    padding: 18px;
    margin-bottom: 16px;
    position: relative;
}}

/* Intensity Card System with Themed Pulsing Glow on Selection (§4) */
.intensity-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    box-shadow: var(--glass-shadow);
    padding: 16px;
    cursor: pointer;
    transition: all 200ms ease;
    height: 100%;
}}
.intensity-card:hover {{
    box-shadow: 0 0 16px rgba(198, 161, 91, 0.2);
}}

/* Pulsing glow scaled to intensity level */
@keyframes pulseGlowLight {{
    0%, 100% {{ border-color: rgba(198, 161, 91, 0.3) !important; box-shadow: 0 0 6px rgba(198, 161, 91, 0.15) !important; }}
    50%      {{ border-color: var(--accent) !important; box-shadow: 0 0 14px rgba(198, 161, 91, 0.35) !important; }}
}}
@keyframes pulseGlowNormal {{
    0%, 100% {{ border-color: rgba(198, 161, 91, 0.4) !important; box-shadow: 0 0 8px rgba(198, 161, 91, 0.25) !important; }}
    50%      {{ border-color: var(--accent-hover) !important; box-shadow: 0 0 20px rgba(198, 161, 91, 0.55) !important; }}
}}
@keyframes pulseGlowHeavy {{
    0%, 100% {{ border-color: var(--severity-high) !important; box-shadow: 0 0 10px rgba(181, 98, 62, 0.3) !important; }}
    50%      {{ border-color: #D97746 !important; box-shadow: 0 0 24px rgba(181, 98, 62, 0.7) !important; }}
}}
@keyframes pulseGlowNoMercy {{
    0%, 100% {{ border-color: var(--severity-critical) !important; box-shadow: 0 0 12px rgba(138, 50, 50, 0.45) !important; }}
    50%      {{ border-color: #D32F2F !important; box-shadow: 0 0 28px rgba(211, 47, 47, 0.85) !important; }}
}}

.intensity-card.selected.intensity-light {{
    animation: pulseGlowLight 3s ease-in-out infinite !important;
}}
.intensity-card.selected.intensity-normal {{
    animation: pulseGlowNormal 2s ease-in-out infinite !important;
}}
.intensity-card.selected.intensity-heavy {{
    animation: pulseGlowHeavy 1.4s ease-in-out infinite !important;
}}
.intensity-card.selected.intensity-no_mercy {{
    animation: pulseGlowNoMercy 0.8s ease-in-out infinite !important;
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

/* Interrogation Persona Card & Turn Animation */
.interrogation-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    box-shadow: var(--glass-shadow);
    padding: 18px;
    margin-bottom: 18px;
    position: relative;
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

/* Spotlight Vignette on Live Interrogation Active Card (§3) */
.active-persona-card {{
    position: relative !important;
}}
.active-persona-card::before {{
    content: "";
    position: absolute;
    inset: -40px;
    background: radial-gradient(ellipse at center, rgba(198,161,91,0.15) 0%, transparent 70%);
    z-index: -1;
    pointer-events: none;
    border-radius: 24px;
    animation: spotlight-pulse 3s ease-in-out infinite;
}}
@keyframes spotlight-pulse {{
    0%, 100% {{ opacity: 0.6; }}
    50%      {{ opacity: 1; }}
}}

/* Persona Ignition on Turn Start (§4) */
@keyframes personaIgnition {{
    0% {{
        box-shadow: 0 0 0 rgba(198, 161, 91, 0);
        transform: scale(0.9);
    }}
    50% {{
        box-shadow: 0 0 20px 4px rgba(198, 161, 91, 0.7);
        transform: scale(1.05);
    }}
    100% {{
        box-shadow: 0 0 8px 1px rgba(198, 161, 91, 0.35);
        transform: scale(1);
    }}
}}
.interrogation-card.latest-turn .avatar-circle {{
    animation: personaIgnition 500ms ease-out forwards;
}}

/* Avatar circle: 50% radius, bg-elevated, 34px */
.avatar-circle {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background-color: var(--bg-elevated);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    vertical-align: middle;
    transition: transform 200ms ease;
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
    line-height: 34px;
}}

/* Question text */
.question-text {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-primary);
    margin-top: 14px;
    margin-bottom: 14px;
    max-width: 75ch;
}}

/* Founder reply box inside interrogation card */
.founder-reply-box {{
    background-color: var(--bg-elevated);
    border: 1px solid var(--border-hairline);
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 14px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text-primary);
    max-width: 75ch;
}}

/* Progress bar (§5: Motion 3) */
.progress-track {{
    width: 100%;
    height: 3px;
    background-color: var(--border-hairline);
    margin-top: 6px;
    margin-bottom: 16px;
    border-radius: 999px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    border-radius: 999px;
    transition: width 400ms ease-in-out;
}}

/* Thinking Indicator with Staggered Pulsing Dots (§4) */
.thinking-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 0;
}}
.thinking-indicator .dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--accent);
    opacity: 0.3;
    transform: scale(0.8);
    animation: thinkingPulse 1.2s infinite ease-in-out;
}}
.thinking-indicator .dot:nth-child(1) {{ animation-delay: 0s; }}
.thinking-indicator .dot:nth-child(2) {{ animation-delay: 0.2s; }}
.thinking-indicator .dot:nth-child(3) {{ animation-delay: 0.4s; }}

@keyframes thinkingPulse {{
    0%, 100% {{
        opacity: 0.3;
        transform: scale(0.8);
        box-shadow: 0 0 0 rgba(198, 161, 91, 0);
    }}
    50% {{
        opacity: 1;
        transform: scale(1.2);
        box-shadow: 0 0 8px var(--accent);
    }}
}}

/* Severity Pills & Gauges */
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

/* Animated Horizontal Severity Gauge (§4) */
.severity-gauge-track {{
    width: 72px;
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    overflow: hidden;
    display: inline-block;
    vertical-align: middle;
}}
.severity-gauge-fill {{
    height: 100%;
    border-radius: 999px;
    animation: gaugeFill 800ms ease-out forwards;
    width: 0%;
}}
@keyframes gaugeFill {{
    from {{ width: 0%; }}
    to {{ width: var(--target-width); }}
}}

/* Data / Numeric text */
.data-mono {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
}}

/* Verdict row & card */
.verdict-row-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    box-shadow: var(--glass-shadow);
    padding: 16px 20px;
    margin-bottom: 12px;
}}

/* Ambient Ember Particles (The Hot Seat Spec §2) */
.ember-field {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}
.ember {{
    position: absolute;
    bottom: -10px;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: radial-gradient(circle, #F0C878 0%, rgba(198,161,91,0) 70%);
    box-shadow: 0 0 6px 2px rgba(198,161,91,0.6);
    animation: ember-drift 9s linear infinite;
}}
@keyframes ember-drift {{
    0%   {{ transform: translateY(0) translateX(0); opacity: 0; }}
    10%  {{ opacity: 0.8; }}
    90%  {{ opacity: 0.4; }}
    100% {{ transform: translateY(-100vh) translateX(20px); opacity: 0; }}
}}

/* Iconography: Give icons more visual weight via Material Symbols fill (§5) */
[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-symbols-outlined,
[data-testid="stMarkdownContainer"] span[class*="material"],
[data-testid="stSidebar"] [data-testid="stIconMaterial"] {{
    font-variation-settings: 'FILL' 1, 'wght' 500 !important;
}}

/* Respect prefers-reduced-motion globally (§4 & §6) */
@media (prefers-reduced-motion: reduce) {{
    *, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"],
    .interrogation-card.latest-turn, .interrogation-card.latest-turn .avatar-circle,
    .active-persona-card::before, .thinking-indicator .dot,
    .intensity-card.selected, .severity-gauge-fill,
    .screen-transition-container, .ember, .ember-field {{
        transition: none !important;
        animation: none !important;
    }}
    .ember-field {{
        display: none !important;
    }}
    .severity-gauge-fill {{
        width: var(--target-width) !important;
    }}
}}
"""


def inject_font_links():
    """Inject non-blocking Google Fonts links with preconnect."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )


def render_ember_field(theme: str):
    """Render ambient floating ember particles in dark mode only."""
    if theme != "dark":
        return
    st.markdown(
        """
        <div class="ember-field" aria-hidden="true">
            <span class="ember" style="left: 8%; animation-delay: 0s; animation-duration: 9.2s;"></span>
            <span class="ember" style="left: 18%; animation-delay: 2.1s; animation-duration: 8.5s;"></span>
            <span class="ember" style="left: 29%; animation-delay: 4.4s; animation-duration: 10.1s;"></span>
            <span class="ember" style="left: 42%; animation-delay: 1.2s; animation-duration: 9.7s;"></span>
            <span class="ember" style="left: 55%; animation-delay: 3.5s; animation-duration: 8.8s;"></span>
            <span class="ember" style="left: 67%; animation-delay: 0.8s; animation-duration: 10.5s;"></span>
            <span class="ember" style="left: 78%; animation-delay: 5.1s; animation-duration: 9.0s;"></span>
            <span class="ember" style="left: 88%; animation-delay: 2.7s; animation-duration: 8.2s;"></span>
            <span class="ember" style="left: 94%; animation-delay: 4.9s; animation-duration: 9.9s;"></span>
            <span class="ember" style="left: 36%; animation-delay: 6.3s; animation-duration: 9.4s;"></span>
            <span class="ember" style="left: 22%; animation-delay: 7.2s; animation-duration: 8.9s;"></span>
            <span class="ember" style="left: 82%; animation-delay: 3.2s; animation-duration: 9.8s;"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_custom_styles():
    theme = st.session_state.get("theme", "dark")
    inject_font_links()
    css = build_css(theme)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    render_ember_field(theme)


def render_thinking_dots():
    """Render 3 pulsing dots inside the reasoning trace / wait state."""
    st.markdown(
        """
        <div class="thinking-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_tracker(persona_status: dict):
    """Renders the 3 progress bars per persona at the top of the Live Interrogation screen."""
    personas = [
        ("vc", "VC", "📈", "var(--severity-medium)"),
        ("analyst", "Financial Analyst", "🧮", "var(--severity-low)"),
        ("realist", "Market Realist", "🌐", "var(--severity-high)"),
    ]

    cols = st.columns(3)
    for i, (key, label, icon, color) in enumerate(personas):
        stat = persona_status.get(key, {"resolved": False, "round": 0})
        rnd = stat.get("round", 0)
        resolved = stat.get("resolved", False)
        pct = 100 if resolved else min(100, int((rnd / 3) * 100))

        with cols[i]:
            status_desc = "✅ Resolved" if resolved else f"Round {rnd} of 3"
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; color: var(--text-primary); display: inline-flex; align-items: center; gap: 6px;">
                        <span style="font-size: 16px; line-height: 1;">{icon}</span> {label}
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
