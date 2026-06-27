"""
main.py — RecruitAI Pro Dashboard (Premium Edition)
Run with: streamlit run main.py
"""
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from parser import parse_resume
from matcher import rank_candidates
from database import (
    init_db, SessionLocal, upsert_candidate, upsert_job, save_scores,
    Candidate, JobDescription, Score,
)

st.set_page_config(
    page_title="RecruitAI Pro - Intelligent Resume Screening",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

JD_PATH = os.path.join(os.path.dirname(__file__), "data", "job_descriptions.json")
with open(JD_PATH) as f:
    DEFAULT_JDS = json.load(f)


def get_db():
    db = SessionLocal()
    return db


for key, default in [
    ("last_results", None),
    ("last_job", None),
    ("theme", "dark"),
    ("page", "Dashboard"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def get_css() -> str:
    is_dark = st.session_state.theme == "dark"

    if is_dark:
        theme_vars = """
        --bg-primary: #0a0a0a;
        --bg-secondary: #121212;
        --bg-card: #1e1e1e;
        --bg-glass: rgba(30,30,30,0.95);
        --text-primary: #ffffff;
        --text-secondary: #d0d0d0;
        --text-muted: #a0a0a0;
        --border-color: rgba(99,102,241,0.3);
        --border-light: rgba(255,255,255,0.1);
        --card-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        --hover-shadow: 0 30px 60px -12px rgba(0,0,0,0.6);
        --progress-bg: #2d2d2d;
        --nav-bg: rgba(10,10,10,0.97);
        --nav-border: rgba(99,102,241,0.2);
        --hero-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        --hero-title-grad: linear-gradient(135deg, #ffffff, #a78bfa, #c084fc);
        --stat-bg: #1e1e1e;
        --stat-value-color: #ffffff;
        --stat-label-color: #a0a0a0;
        --candidate-bg: #1e1e1e;
        --candidate-hover-bg: #2a2a2a;
        --glass-bg: rgba(30,30,30,0.95);
        --step-bg: #1e1e1e;
        --skill-pill-bg: rgba(99,102,241,0.2);
        --skill-pill-border: rgba(99,102,241,0.3);
        --skill-pill-color: #c084fc;
        --feature-pill-bg: rgba(99,102,241,0.15);
        --feature-pill-border: rgba(99,102,241,0.25);
        --feature-pill-color: #a78bfa;
        --score-chip-bg: #2a2a2a;
        --score-chip-border: rgba(255,255,255,0.1);
        --score-chip-label: #a0a0a0;
        --score-chip-value: #ffffff;
        --profile-val-color: #d0d0d0;
        --step-title-color: #ffffff;
        --step-desc-color: #a0a0a0;
        --section-header-color: #a78bfa;
        --success-bg: rgba(16,185,129,0.15);
        --success-border: rgba(16,185,129,0.3);
        --success-color: #34d399;
        --info-bg: rgba(99,102,241,0.15);
        --info-border: rgba(99,102,241,0.3);
        --info-color: #818cf8;
        --warning-bg: rgba(245,158,11,0.15);
        --warning-border: rgba(245,158,11,0.3);
        --warning-color: #fbbf24;
        --divider-emoji-bg: #1e1e1e;
        --divider-emoji-color: #a78bfa;
        --grid-line: rgba(99,102,241,0.06);
        --orb1-color: rgba(99,102,241,0.12);
        --orb2-color: rgba(139,92,246,0.08);
        --resume-bg: #1a1a1a;
        --resume-border: rgba(99,102,241,0.2);
        --resume-text: #d0d0d0;
        --nav-link-active-color: #ffffff;
        --nav-link-color: #a0a0a0;
        --nav-link-hover-color: #ffffff;
        --hamburger-color: #d0d0d0;
        --mobile-menu-bg: #0d0d0d;
        --card-name-color: #ffffff;
        --card-sub-color: #a0a0a0;
        --expander-title-color: #ffffff;
        --profile-label-color: #a0a0a0;
        --score-header-color: #d0d0d0;
        --activity-name-color: #ffffff;
        --activity-sub-color: #a0a0a0;
        --label-color: #d0d0d0;
        --placeholder-color: #666666;
        --select-text-color: #ffffff;
        --select-bg: #2d2d2d;
        --markdown-text-color: #d0d0d0;
        """
        app_bg = "background: linear-gradient(135deg, #0a0a0a 0%, #121212 50%, #1a1a2e 100%) !important;"
        input_color = "#ffffff"
        input_bg = "#2d2d2d"
        accent_grad = "linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa)"
        btn_grad = "linear-gradient(135deg, #6366f1, #8b5cf6)"
        hero_sub_color = "rgba(255,255,255,0.8)"
        rank_n_color = "white"
    else:
        theme_vars = """
        --bg-primary: #f0f2f8;
        --bg-secondary: #ffffff;
        --bg-card: #ffffff;
        --bg-glass: rgba(255,255,255,0.98);
        --text-primary: #1a1a2e;
        --text-secondary: #374151;
        --text-muted: #6b7280;
        --border-color: rgba(99,102,241,0.25);
        --border-light: #e5e7eb;
        --card-shadow: 0 4px 24px rgba(0,0,0,0.08);
        --hover-shadow: 0 12px 40px rgba(0,0,0,0.14);
        --progress-bg: #e5e7eb;
        --nav-bg: rgba(255,255,255,0.98);
        --nav-border: rgba(99,102,241,0.15);
        --hero-bg: linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #9333ea 100%);
        --hero-title-grad: linear-gradient(135deg, #ffffff, #e0d4ff);
        --stat-bg: #ffffff;
        --stat-value-color: #1a1a2e;
        --stat-label-color: #6b7280;
        --candidate-bg: #ffffff;
        --candidate-hover-bg: #f5f3ff;
        --glass-bg: rgba(255,255,255,0.98);
        --step-bg: #ffffff;
        --skill-pill-bg: rgba(99,102,241,0.1);
        --skill-pill-border: rgba(99,102,241,0.25);
        --skill-pill-color: #4f46e5;
        --feature-pill-bg: rgba(99,102,241,0.08);
        --feature-pill-border: rgba(99,102,241,0.2);
        --feature-pill-color: #4f46e5;
        --score-chip-bg: #f5f3ff;
        --score-chip-border: #ddd6fe;
        --score-chip-label: #6b7280;
        --score-chip-value: #1a1a2e;
        --profile-val-color: #1a1a2e;
        --step-title-color: #1a1a2e;
        --step-desc-color: #6b7280;
        --section-header-color: #4f46e5;
        --success-bg: #ecfdf5;
        --success-border: #6ee7b7;
        --success-color: #065f46;
        --info-bg: #eef2ff;
        --info-border: #a5b4fc;
        --info-color: #3730a3;
        --warning-bg: #fffbeb;
        --warning-border: #fcd34d;
        --warning-color: #92400e;
        --divider-emoji-bg: #f0f2f8;
        --divider-emoji-color: #4f46e5;
        --grid-line: rgba(99,102,241,0.05);
        --orb1-color: rgba(99,102,241,0.07);
        --orb2-color: rgba(139,92,246,0.05);
        --resume-bg: #f9fafb;
        --resume-border: #e5e7eb;
        --resume-text: #374151;
        --nav-link-active-color: #ffffff;
        --nav-link-color: #374151;
        --nav-link-hover-color: #4f46e5;
        --hamburger-color: #374151;
        --mobile-menu-bg: #ffffff;
        --card-name-color: #1a1a2e;
        --card-sub-color: #6b7280;
        --expander-title-color: #1a1a2e;
        --profile-label-color: #6b7280;
        --score-header-color: #374151;
        --activity-name-color: #1a1a2e;
        --activity-sub-color: #6b7280;
        --label-color: #1a1a2e;
        --placeholder-color: #9ca3af;
        --select-text-color: #1a1a2e;
        --select-bg: #ffffff;
        --markdown-text-color: #1a1a2e;
        """
        app_bg = "background: linear-gradient(135deg, #f0f2f8 0%, #ece9f5 100%) !important;"
        input_color = "#1a1a2e"
        input_bg = "#ffffff"
        accent_grad = "linear-gradient(135deg, #4f46e5, #7c3aed)"
        btn_grad = "linear-gradient(135deg, #4f46e5, #7c3aed)"
        hero_sub_color = "rgba(255,255,255,0.9)"
        rank_n_color = "#1a1a2e"

    page_to_navkey = {
        "Dashboard": "navbtn_dashboard",
        "Upload Resumes": "navbtn_upload",
        "Manage Jobs": "navbtn_jobs",
        "Results & Rankings": "navbtn_rankings",
        "Candidate Detail": "navbtn_details",
    }
    active_key = page_to_navkey.get(st.session_state.page, "navbtn_dashboard")
    active_nav_css = f""".st-key-{active_key} .stButton > button {{
        background: {accent_grad} !important;
        color: var(--nav-link-active-color) !important;
        box-shadow: 0 6px 16px rgba(99,102,241,0.35) !important;
    }}"""

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{ {theme_vars} }}

html, body, .stApp {{
    {app_bg}
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

[data-testid="stSidebar"] {{ display: none !important; }}

.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── AMBIENT ORBS ── */
.stApp::before {{
    content: '';
    position: fixed; top: -20%; right: -10%;
    width: 60vmax; height: 60vmax;
    background: radial-gradient(circle, var(--orb1-color), transparent);
    border-radius: 50%;
    animation: orbFloat1 22s ease-in-out infinite;
    pointer-events: none; z-index: 0;
}}
.stApp::after {{
    content: '';
    position: fixed; bottom: -15%; left: -5%;
    width: 50vmax; height: 50vmax;
    background: radial-gradient(circle, var(--orb2-color), transparent);
    border-radius: 50%;
    animation: orbFloat2 28s ease-in-out infinite;
    pointer-events: none; z-index: 0;
}}
@keyframes orbFloat1 {{
    0%,100% {{ transform: translate(0,0) scale(1); }}
    33% {{ transform: translate(-30px,20px) scale(1.1); }}
    66% {{ transform: translate(30px,-20px) scale(0.9); }}
}}
@keyframes orbFloat2 {{
    0%,100% {{ transform: translate(0,0) scale(1); }}
    33% {{ transform: translate(40px,-30px) scale(1.15); }}
    66% {{ transform: translate(-40px,30px) scale(0.85); }}
}}

/* ── GRID OVERLAY ── */
.grid-overlay {{
    position: fixed; top:0; left:0; width:100%; height:100%;
    background-image:
        linear-gradient(var(--grid-line) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 45px 45px;
    pointer-events: none;
    animation: gridMove 20s linear infinite;
    z-index: 0;
}}
@keyframes gridMove {{
    0% {{ background-position: 0 0; }}
    100% {{ background-position: 45px 45px; }}
}}

/* ── NAVBAR ── */
.nav-brand {{
    display: flex; align-items: center; gap: 10px;
    flex-shrink: 0; cursor: default;
}}
.nav-logo-box {{
    width: 38px; height: 38px;
    background: {accent_grad};
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    animation: logoGlow 3s ease-in-out infinite;
    flex-shrink: 0;
}}
@keyframes logoGlow {{
    0%,100% {{ box-shadow: 0 0 0 0 rgba(99,102,241,0.3); }}
    50% {{ box-shadow: 0 0 16px 4px rgba(99,102,241,0.25); }}
}}
.nav-brand-text {{
    display: flex; flex-direction: column; line-height: 1.1;
}}
.nav-brand-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.05rem; font-weight: 700;
    background: {accent_grad};
    -webkit-background-clip: text; background-clip: text; color: transparent;
    white-space: nowrap;
}}
.nav-brand-sub {{
    font-size: 0.6rem; color: var(--text-muted);
    letter-spacing: 0.04em; white-space: nowrap;
}}

/* ── NAVBAR (true top, links pinned right) ── */
.st-key-navbar_root {{
    position: sticky !important; top: 0 !important; z-index: 9999 !important;
    width: 100% !important;
}}
.st-key-navbar_root > div {{
    display: flex !important; align-items: center !important;
    justify-content: space-between !important; flex-wrap: wrap;
    gap: 0.6rem; width: 100%;
    max-width: 1400px; margin: 0 auto;
    padding: 10px 1.5rem; min-height: 64px;
    background: var(--nav-bg);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--nav-border);
}}
.st-key-navbar_root [data-testid="stHorizontalBlock"] {{
    margin-left: auto !important; width: auto !important;
    gap: 6px !important; flex-wrap: wrap; justify-content: flex-end;
}}
.st-key-navbar_root [data-testid="stHorizontalBlock"] > div {{ width: auto !important; }}
.st-key-navbar_root .stButton > button {{
    background: transparent !important; color: var(--nav-link-color) !important;
    box-shadow: none !important; border: 1px solid transparent !important;
    padding: 8px 14px !important; font-size: 13px !important; font-weight: 600 !important;
    border-radius: 10px !important; white-space: nowrap;
    transition: all 0.25s ease !important;
}}
.st-key-navbar_root .stButton > button:hover {{
    background: var(--border-light) !important;
    color: var(--nav-link-hover-color) !important;
    transform: translateY(-2px) !important;
    box-shadow: none !important;
}}
.st-key-navtheme .stButton > button {{
    border: 1px solid var(--nav-border) !important; border-radius: 999px !important;
}}
{active_nav_css}
@media (max-width: 900px) {{
    .st-key-navbar_root > div {{ padding: 10px 1rem; justify-content: center; }}
    .st-key-navbar_root [data-testid="stHorizontalBlock"] {{ justify-content: center; margin-left: 0 !important; width: 100% !important; }}
    .nav-brand {{ width: 100%; justify-content: center; }}
}}
@media (max-width: 560px) {{
    .st-key-navbar_root .stButton > button {{ padding: 7px 10px !important; font-size: 11.5px !important; }}
}}

/* ── MAIN CONTENT ── */
.main-content {{
    padding: 2rem 2rem 3rem;
    max-width: 1400px; margin: 0 auto;
    position: relative; z-index: 1;
    animation: contentFadeIn 0.5s ease-out;
}}
@keyframes contentFadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.st-key-navbar_root > div {{
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}}
@media (max-width: 768px) {{
    .main-content {{ padding: 1rem 1rem 2rem; }}
}}

/* ── HERO BANNER ── */
.hero-3d {{
    background: var(--hero-bg);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 28px; padding: 44px 52px;
    margin-bottom: 36px; position: relative; overflow: hidden;
    box-shadow: 0 20px 60px rgba(79,70,229,0.3);
    animation: heroFloat 6s ease-in-out infinite;
}}
@keyframes heroFloat {{
    0%,100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-6px); }}
}}
.hero-3d::before {{
    content: '';
    position: absolute; top: 0; left: -100%;
    width: 200%; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), rgba(196,132,252,0.8), rgba(255,255,255,0.6), transparent);
    animation: scanBeam 4s linear infinite;
}}
@keyframes scanBeam {{
    0% {{ left: -100%; }} 100% {{ left: 200%; }}
}}
.hero-icon {{
    font-size: 52px; display: inline-block;
    margin-right: 18px;
    animation: iconBounce 2.5s ease-in-out infinite;
}}
@keyframes iconBounce {{
    0%,100% {{ transform: scale(1) rotate(0deg); }}
    50% {{ transform: scale(1.12) rotate(5deg); }}
}}
.hero-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px; font-weight: 800;
    background: var(--hero-title-grad);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    letter-spacing: -0.5px;
}}
.hero-sub {{
    font-size: 14px;
    color: {hero_sub_color};
    margin-top: 8px;
}}
@media (max-width: 768px) {{
    .hero-3d {{ padding: 24px 20px; margin-bottom: 20px; }}
    .hero-title {{ font-size: 22px; }}
    .hero-icon {{ font-size: 36px; margin-right: 12px; }}
}}

/* ── STATS GRID ── */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px; margin-bottom: 36px;
}}
.stat-card {{
    background: var(--stat-bg);
    border: 1px solid var(--border-light);
    border-radius: 20px; padding: 22px 16px;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.34,1.56,0.64,1);
    box-shadow: var(--card-shadow);
    position: relative; overflow: hidden;
}}
.stat-card::before {{
    content: '';
    position: absolute; top:0; left:0; right:0; height: 3px;
    background: {accent_grad};
    transform: scaleX(0); transition: transform 0.35s; transform-origin: left;
}}
.stat-card:hover::before {{ transform: scaleX(1); }}
.stat-card:hover {{ transform: translateY(-8px) scale(1.02); box-shadow: var(--hover-shadow); }}
.stat-value {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 38px; font-weight: 800;
    color: var(--stat-value-color);
    line-height: 1.1;
}}
.stat-label {{
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    margin-top: 6px; color: var(--stat-label-color);
}}
@media (max-width: 1100px) {{ .stats-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 640px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }} .stat-value {{ font-size: 28px; }} }}

/* ── CANDIDATE CARDS ── */
.candidate-card {{
    display: flex; align-items: center; gap: 18px;
    padding: 18px 22px;
    background: var(--candidate-bg);
    border: 1px solid var(--border-light);
    border-radius: 18px; margin-bottom: 10px;
    transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1);
    position: relative; flex-wrap: wrap;
}}
.candidate-card::before {{
    content: '';
    position: absolute; left:0; top:0; bottom:0; width: 4px;
    background: {accent_grad};
    border-radius: 18px 0 0 18px;
    transform: scaleY(0); transition: transform 0.3s;
}}
.candidate-card:hover::before {{ transform: scaleY(1); }}
.candidate-card:hover {{
    background: var(--candidate-hover-bg);
    transform: translateX(6px);
    box-shadow: -4px 0 0 #6366f1;
}}

/* ── RANK BADGES ── */
.rank-badge {{
    width: 48px; height: 48px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; flex-shrink: 0;
    transition: transform 0.25s;
}}
.candidate-card:hover .rank-badge {{ transform: scale(1.15) rotate(5deg); }}
.rank-1 {{ background: linear-gradient(135deg, #fbbf24, #f97316); }}
.rank-2 {{ background: linear-gradient(135deg, #94a3b8, #64748b); }}
.rank-3 {{ background: linear-gradient(135deg, #cd7f32, #b8860b); }}
.rank-n {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; }}

/* ── AVATAR ── */
.avatar {{
    width: 50px; height: 50px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 22px; color: white;
    background: {accent_grad};
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
    flex-shrink: 0;
}}
.candidate-card:hover .avatar {{ transform: scale(1.1) rotate(-5deg); }}

/* ── PROGRESS BAR ── */
.score-container {{ flex: 1; min-width: 160px; }}
.score-header {{
    display: flex; justify-content: space-between; margin-bottom: 5px;
    font-size: 12px; font-weight: 600; color: var(--score-header-color);
}}
.progress-bar-bg {{ background: var(--progress-bg); border-radius: 99px; height: 7px; overflow: hidden; }}
.progress-fill {{
    height: 100%; border-radius: 99px;
    transition: width 1s cubic-bezier(0.4,0,0.2,1);
    position: relative; overflow: hidden;
}}
.progress-fill::after {{
    content: '';
    position: absolute; top:0; left:0; right:0; bottom:0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmerProgress 2s infinite;
}}
@keyframes shimmerProgress {{ 0% {{ transform: translateX(-100%); }} 100% {{ transform: translateX(100%); }} }}
.progress-high {{ background: linear-gradient(90deg, #10b981, #34d399); }}
.progress-mid  {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
.progress-low  {{ background: linear-gradient(90deg, #ef4444, #f87171); }}

/* ── SKILL PILLS ── */
.skill-pill {{
    display: inline-block;
    background: var(--skill-pill-bg); border: 1px solid var(--skill-pill-border);
    color: var(--skill-pill-color);
    border-radius: 40px; padding: 4px 12px;
    font-size: 10px; font-weight: 600; margin: 3px 3px;
    transition: all 0.2s;
}}
.skill-pill:hover {{ transform: translateY(-2px); }}

/* ── FEATURE PILLS ── */
.feature-pill {{
    display: inline-block;
    background: var(--feature-pill-bg); border: 1px solid var(--feature-pill-border);
    color: var(--feature-pill-color);
    border-radius: 40px; padding: 6px 16px;
    font-size: 12px; font-weight: 500; margin: 5px;
    transition: all 0.2s;
}}
.feature-pill:hover {{ transform: translateY(-2px); }}

/* ── SCORE CHIPS ── */
.score-chip {{
    background: var(--score-chip-bg); border: 1px solid var(--score-chip-border);
    border-radius: 12px; padding: 6px 12px; text-align: center;
    transition: all 0.2s; flex-shrink: 0;
}}
.score-chip:hover {{ transform: translateY(-3px); }}
.chip-label {{
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; color: var(--score-chip-label);
}}
.chip-value {{
    font-size: 14px; font-weight: 800; color: var(--score-chip-value);
}}

/* ── GLASS CARD ── */
.glass-card {{
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 22px; padding: 26px;
    transition: all 0.3s; box-shadow: var(--card-shadow);
}}
.glass-card:hover {{ transform: translateY(-4px); box-shadow: var(--hover-shadow); }}

/* ── SECTION HEADER ── */
.section-header {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 2px;
    margin: 36px 0 18px;
    display: flex; align-items: center; gap: 12px;
    color: var(--section-header-color);
}}
.section-header::before {{
    content: '';
    width: 4px; height: 22px;
    background: {accent_grad};
    border-radius: 3px;
    animation: headerPulse 2s ease-in-out infinite;
}}
@keyframes headerPulse {{
    0%,100% {{ height: 22px; opacity: 0.6; }}
    50% {{ height: 28px; opacity: 1; }}
}}

/* ── FANCY DIVIDER ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), rgba(139,92,246,0.5), transparent);
    margin: 36px 0; position: relative;
}}
.fancy-divider::before {{
    content: '✦';
    position: absolute; left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    background: var(--divider-emoji-bg);
    padding: 0 16px; font-size: 12px; color: var(--divider-emoji-color);
}}

/* ── STEP CARDS ── */
.step-card {{
    background: var(--step-bg); border: 1px solid var(--border-light);
    border-radius: 18px; padding: 26px 18px; text-align: center;
    transition: all 0.4s cubic-bezier(0.34,1.56,0.64,1); box-shadow: var(--card-shadow);
}}
.step-card:hover {{ transform: translateY(-10px); box-shadow: var(--hover-shadow); }}
.step-number {{
    width: 48px; height: 48px; background: {accent_grad};
    border-radius: 14px; display: flex; align-items: center; justify-content: center;
    margin: 0 auto 14px; font-size: 18px; font-weight: 800; color: white;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35); transition: transform 0.3s;
}}
.step-card:hover .step-number {{ transform: scale(1.12) rotate(-5deg); }}
.step-title {{ font-size: 14px; font-weight: 700; margin-bottom: 8px; color: var(--step-title-color); }}
.step-desc {{ font-size: 12px; color: var(--step-desc-color); line-height: 1.5; }}

/* ── PROFILE ROW ── */
.profile-row {{
    display: flex; align-items: center; padding: 11px 0;
    border-bottom: 1px solid var(--border-light);
}}
.profile-label {{
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; width: 80px; color: var(--profile-label-color);
}}
.profile-value {{ font-size: 13px; font-weight: 500; color: var(--profile-val-color); }}

/* ── MESSAGES ── */
.success-msg, .warning-msg, .info-msg {{
    border-radius: 12px; padding: 14px 20px; margin: 14px 0;
    font-size: 14px; font-weight: 500;
    animation: slideInMsg 0.4s cubic-bezier(0.34,1.56,0.64,1);
}}
@keyframes slideInMsg {{
    from {{ transform: translateY(-16px); opacity: 0; }}
    to   {{ transform: translateY(0); opacity: 1; }}
}}
.success-msg {{ background: var(--success-bg); border: 1px solid var(--success-border); color: var(--success-color); }}
.info-msg    {{ background: var(--info-bg);    border: 1px solid var(--info-border);    color: var(--info-color); }}
.warning-msg {{ background: var(--warning-bg); border: 1px solid var(--warning-border); color: var(--warning-color); }}

/* ── BUTTONS ── */
.stButton > button {{
    background: {btn_grad} !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; padding: 10px 24px !important;
    font-weight: 600 !important; font-size: 14px !important;
    transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1) !important;
}}
.stButton > button:hover {{
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.4) !important;
}}
.stButton > button:active {{ transform: scale(0.98) !important; }}

/* ── INPUT FIELDS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {{
    background: {input_bg} !important;
    border: 1px solid var(--border-light) !important;
    color: {input_color} !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    transition: all 0.3s !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    outline: none !important;
}}

/* ── PLACEHOLDER TEXT ── */
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color: var(--placeholder-color) !important;
    opacity: 1 !important;
}}

/* ── ALL LABELS (st.text_input, st.selectbox, st.text_area labels) ── */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stFileUploader label,
.stMultiSelect label,
label[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {{
    color: var(--label-color) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}

/* ── SELECTBOX DROPDOWN TEXT ── */
.stSelectbox > div > div > div,
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div,
[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
[role="option"],
[data-baseweb="menu"] li,
[data-baseweb="popover"] li {{
    color: var(--select-text-color) !important;
    background-color: var(--select-bg) !important;
}}

/* ── SELECTBOX SELECTED VALUE TEXT ── */
.stSelectbox [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
.stSelectbox [data-baseweb="select"] > div > div {{
    color: var(--select-text-color) !important;
}}

/* ── MARKDOWN TEXT (st.markdown rendered paragraphs) ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
.stMarkdown p,
.stMarkdown span {{
    color: var(--markdown-text-color) !important;
}}

/* ── GENERAL STREAMLIT TEXT OVERRIDES FOR LIGHT MODE ── */
p, span, div.stText {{
    color: var(--text-primary);
}}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed rgba(99,102,241,0.35) !important;
    border-radius: 18px !important; padding: 22px !important;
    transition: all 0.3s !important; background: var(--bg-card) !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(99,102,241,0.65) !important; transform: scale(1.01);
}}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small,
[data-testid="stFileDropzoneInstructions"] span {{
    color: var(--label-color) !important;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    border-radius: 14px !important; padding: 5px !important;
    gap: 5px !important; background: var(--bg-secondary) !important;
    border: 1px solid var(--border-light) !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px !important; font-weight: 600 !important;
    padding: 9px 22px !important; transition: all 0.3s !important;
    color: var(--text-secondary) !important;
}}
.stTabs [aria-selected="true"] {{
    background: {btn_grad} !important; color: white !important; transform: scale(1.02);
}}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    border-radius: 14px !important; border: 1px solid var(--border-light) !important;
    transition: all 0.3s !important; margin-bottom: 8px !important;
    background: var(--bg-card) !important;
}}
[data-testid="stExpander"] summary {{
    color: var(--text-primary) !important; font-weight: 600 !important;
}}
[data-testid="stExpander"] p,
[data-testid="stExpander"] span,
[data-testid="stExpander"] div {{
    color: var(--text-secondary) !important;
}}

/* ── METRIC ── */
[data-testid="stMetric"] {{
    background: var(--bg-card); padding: 16px;
    border-radius: 14px; border: 1px solid var(--border-light);
}}
[data-testid="stMetric"] label {{ color: var(--text-muted) !important; }}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: var(--text-primary) !important;
}}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px !important; overflow: hidden;
    border: 1px solid var(--border-light) !important;
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 7px; height: 7px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, #6366f1, #8b5cf6); border-radius: 10px;
}}
</style>
<div class="grid-overlay"></div>
"""


st.markdown(get_css(), unsafe_allow_html=True)


def render_nav_bar():
    is_dark = st.session_state.theme == "dark"
    theme_icon = "☀️ Light" if is_dark else "🌙 Dark"

    nav_items = [
        ("Dashboard", "🏠 Dashboard", "navbtn_dashboard"),
        ("Upload Resumes", "📄 Upload", "navbtn_upload"),
        ("Manage Jobs", "💼 Jobs", "navbtn_jobs"),
        ("Results & Rankings", "📊 Rankings", "navbtn_rankings"),
        ("Candidate Detail", "🔍 Details", "navbtn_details"),
    ]

    with st.container(key="navbar_root"):
        st.markdown("""
            <div class="nav-brand">
                <div class="nav-logo-box">🎯</div>
                <div class="nav-brand-text">
                    <span class="nav-brand-title">RecruitAI Pro</span>
                    <span class="nav-brand-sub">Intelligent Resume Screening</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        cols = st.columns(len(nav_items) + 1)
        for i, (page_id, label, navkey) in enumerate(nav_items):
            with cols[i]:
                with st.container(key=navkey):
                    if st.button(label, key=f"btn_{navkey}", use_container_width=True):
                        st.session_state.page = page_id; st.rerun()
        with cols[-1]:
            with st.container(key="navtheme"):
                if st.button(theme_icon, key="btn_theme_toggle", use_container_width=True):
                    st.session_state.theme = "light" if is_dark else "dark"; st.rerun()

    st.markdown('<div class="main-content">', unsafe_allow_html=True)


render_nav_bar()


# ── SYSTEM STATUS ──────────────────────────────────────────────────────────────
def render_system_status():
    db = get_db()
    n_c = db.query(Candidate).count()
    n_j = db.query(JobDescription).count()
    n_s = db.query(Score).count()
    db.close()
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("👥 Total Candidates", n_c)
    with col2: st.metric("💼 Active Jobs", n_j)
    with col3: st.metric("⚡ Screenings Run", n_s)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def fit_color(score: float) -> str:
    if score >= 0.70: return "#10b981"
    if score >= 0.45: return "#f59e0b"
    return "#ef4444"

def fit_class(score: float) -> str:
    if score >= 0.70: return "high"
    if score >= 0.45: return "mid"
    return "low"

def score_bar(score: float) -> str:
    pct = round(score * 100, 1)
    cls = fit_class(score)
    color = fit_color(score)
    return f'''
    <div class="score-container">
        <div class="score-header">
            <span>Match Score</span>
            <span style="color:{color};font-weight:700;">{pct}%</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-fill progress-{cls}" style="width:{pct}%;"></div>
        </div>
    </div>'''

def rank_badge(rank: int) -> str:
    if rank == 1: return '<div class="rank-badge rank-1">🥇</div>'
    elif rank == 2: return '<div class="rank-badge rank-2">🥈</div>'
    elif rank == 3: return '<div class="rank-badge rank-3">🥉</div>'
    return f'<div class="rank-badge rank-n">#{rank}</div>'

def skill_pills(skills: list, limit: int = 8) -> str:
    if not skills: return '<span style="color:var(--text-muted);">No skills detected</span>'
    return "".join(f'<span class="skill-pill">{s}</span>' for s in skills[:limit])

def avatar(name: str) -> str:
    return f'<div class="avatar">{(name or "?")[0].upper()}</div>'

def hero_banner(icon: str, title: str, subtitle: str):
    st.markdown(f'''
    <div class="hero-3d">
        <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;">
            <span class="hero-icon">{icon}</span>
            <div>
                <div class="hero-title">{title}</div>
                <div class="hero-sub">{subtitle}</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def plotly_layout_defaults() -> dict:
    is_dark = st.session_state.theme == "dark"
    text_color = "#d0d0d0" if is_dark else "#1a1a2e"
    grid_color = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)"
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
    )


page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    hero_banner("🏠", "Command Center", "Your AI-powered recruitment intelligence hub — at a glance")
    render_system_status()

    db = get_db()
    candidates = db.query(Candidate).all()
    jobs = db.query(JobDescription).all()
    scores_all = db.query(Score).all()
    db.close()

    avg_fit = round(sum(s.fit_score for s in scores_all) / len(scores_all) * 100, 1) if scores_all else 0
    top_score = round(max((s.fit_score for s in scores_all), default=0) * 100, 1)
    total_skills = sum(len(json.loads(c.skills_json or "[]")) for c in candidates)

    st.markdown(f'''
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{len(candidates)}</div>
            <div class="stat-label">Candidates</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(jobs)}</div>
            <div class="stat-label">Jobs</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(scores_all)}</div>
            <div class="stat-label">Screenings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_fit}%</div>
            <div class="stat-label">Avg Fit</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_skills}</div>
            <div class="stat-label">Skills</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{top_score}%</div>
            <div class="stat-label">Top Score</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🚀 Quick Actions</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Upload Resumes", use_container_width=True):
            st.session_state.page = "Upload Resumes"; st.rerun()
    with col2:
        if st.button("💼 Manage Jobs", use_container_width=True):
            st.session_state.page = "Manage Jobs"; st.rerun()
    with col3:
        if st.button("📊 View Rankings", use_container_width=True):
            st.session_state.page = "Results & Rankings"; st.rerun()

    st.markdown('<div class="section-header">✨ How It Works</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("1", "📤", "Upload",  "Add PDF/DOCX files"),
        ("2", "💼", "Jobs",    "Add descriptions"),
        ("3", "🚀", "Screen",  "AI scores instantly"),
        ("4", "📊", "Rank",    "Review results"),
    ]
    for col, (num, icon, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(f'''
            <div class="step-card">
                <div class="step-number">{num}</div>
                <div style="font-size:30px;margin-bottom:8px;">{icon}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">📋 Recent Activity</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if candidates:
        recent = sorted(candidates, key=lambda x: x.created_at, reverse=True)[:5]
        for c in recent:
            skills = json.loads(c.skills_json or "[]")
            st.markdown(f'''
            <div style="display:flex;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid var(--border-light);">
                {avatar(c.name or c.filename)}
                <div style="flex:1;">
                    <div style="font-weight:600;color:var(--activity-name-color);">{c.name or c.filename}</div>
                    <div style="font-size:11px;color:var(--activity-sub-color);">{len(skills)} skills · {c.email or "no email"}</div>
                </div>
                <div style="font-size:10px;background:rgba(99,102,241,0.18);color:var(--info-color);padding:3px 10px;border-radius:20px;font-weight:700;">NEW</div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-msg">ℹ️ No candidates yet — upload some resumes to get started.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🧠 AI Capabilities</div>', unsafe_allow_html=True)
    features = [
        "TF-IDF NLP Matching", "Skill Overlap Scoring", "Experience Detection",
        "Auto Email Extraction", "LinkedIn Detection", "Phone Parser",
        "SQLite Persistence", "Interactive Charts", "Composite Fit Score",
    ]
    pills_html = "".join(f'<span class="feature-pill">{f}</span>' for f in features)
    st.markdown(f'<div style="line-height:3;text-align:center;">{pills_html}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD RESUMES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Upload Resumes":
    hero_banner("📄", "Upload Resumes", "Drop PDF or DOCX files — our AI parser extracts everything automatically")

    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        db = get_db()
        progress = st.progress(0)
        results_log = []
        for i, f in enumerate(uploaded_files):
            try:
                parsed = parse_resume(f.read(), f.name)
                upsert_candidate(db, parsed)
                results_log.append({
                    "File": f.name, "Name": parsed["name"] or "—",
                    "Email": parsed["email"] or "—", "Phone": parsed["phone"] or "—",
                    "Skills Found": len(parsed.get("skills", [])), "Status": "✅",
                })
            except Exception as e:
                results_log.append({"File": f.name, "Status": f"❌ {str(e)[:50]}"})
            progress.progress((i + 1) / len(uploaded_files))
        db.close()
        st.success(f"✅ Successfully processed {len(uploaded_files)} resume(s)")
        st.dataframe(pd.DataFrame(results_log), use_container_width=True, hide_index=True)

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📁 All Stored Candidates</div>', unsafe_allow_html=True)

    db = get_db()
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    db.close()

    if candidates:
        for c in candidates:
            skills = json.loads(c.skills_json or "[]")
            with st.expander(f"📄 {c.name or c.filename} — {c.email or 'no email'} — {len(skills)} skills"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f'''
                    <div style="display:flex;gap:14px;margin-bottom:14px;">
                        {avatar(c.name or c.filename)}
                        <div>
                            <div style="font-size:17px;font-weight:700;color:var(--card-name-color);">{c.name or "Unknown"}</div>
                            <div style="font-size:11px;color:var(--card-sub-color);">{c.filename}</div>
                        </div>
                    </div>
                    <div class="profile-row"><span class="profile-label">Email</span><span class="profile-value">{c.email or "—"}</span></div>
                    <div class="profile-row"><span class="profile-label">Phone</span><span class="profile-value">{c.phone or "—"}</span></div>
                    <div class="profile-row"><span class="profile-label">LinkedIn</span><span class="profile-value">{c.linkedin or "—"}</span></div>
                    ''', unsafe_allow_html=True)
                with col2:
                    if skills:
                        st.markdown('<strong style="font-size:11px;color:var(--text-muted);">🛠️ SKILLS DETECTED</strong>', unsafe_allow_html=True)
                        st.markdown('<div style="margin-top:8px;">' + skill_pills(skills) + '</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="info-msg">ℹ️ No technical skills detected in this resume.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-msg">ℹ️ No candidates yet — upload resumes above to get started.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MANAGE JOBS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Manage Jobs":
    hero_banner("💼", "Manage Jobs", "Define job descriptions to screen candidates against — or use our samples")

    tab1, tab2 = st.tabs(["➕ Add / Edit Job", "📋 All Jobs"])

    with tab1:
        db = get_db()
        preload = st.selectbox(
            "📌 Pre-load a sample job description",
            ["— select to pre-fill —"] + [j["title"] for j in DEFAULT_JDS]
        )
        preloaded_jd = next((j for j in DEFAULT_JDS if j["title"] == preload), None)
        title = st.text_input(
            "Job Title",
            value=preloaded_jd["title"] if preloaded_jd else "",
            placeholder="e.g. Senior Backend Engineer"
        )
        description = st.text_area(
            "Job Description",
            value=preloaded_jd["description"] if preloaded_jd else "",
            height=200,
            placeholder="Paste the full job posting here..."
        )

        col_save, col_seed = st.columns(2)
        with col_save:
            if st.button("💾 Save Job", use_container_width=True):
                if title and description:
                    upsert_job(db, title, description)
                    st.success(f"✅ Saved: {title}"); st.rerun()
                else:
                    st.warning("⚠ Both fields are required")
        with col_seed:
            if st.button("⚡ Seed All Sample Jobs", use_container_width=True):
                for jd in DEFAULT_JDS:
                    upsert_job(db, jd["title"], jd["description"])
                st.success("✅ All sample jobs added!"); st.rerun()
        db.close()

    with tab2:
        db = get_db()
        jobs = db.query(JobDescription).all()
        db.close()
        if jobs:
            for job in jobs:
                with st.expander(f"💼 {job.title}"):
                    st.text_area(
                        "", job.description, height=120,
                        key=f"jd_{job.id}", disabled=True,
                        label_visibility="collapsed"
                    )
        else:
            st.markdown('<div class="info-msg">ℹ️ No jobs yet — add one in the tab above.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS & RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Results & Rankings":
    hero_banner("📊", "Results & Rankings", "AI-powered candidate scoring with multi-dimensional analysis")

    db = get_db()
    candidates_all = db.query(Candidate).all()
    jobs_all = db.query(JobDescription).all()
    db.close()

    if not candidates_all:
        st.warning("⚠ No candidates found — upload resumes first."); st.stop()
    if not jobs_all:
        st.warning("⚠ No job descriptions found — add jobs first."); st.stop()

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_job_title = st.selectbox(
            "Select job to screen for",
            [j.title for j in jobs_all],
            label_visibility="collapsed"
        )
    with col_btn:
        run_btn = st.button("🚀 Run AI Screening", use_container_width=True)

    selected_job = next(j for j in jobs_all if j.title == selected_job_title)

    if run_btn:
        with st.spinner("🧠 AI is analysing and scoring all candidates…"):
            resume_dicts = [{
                "filename": c.filename, "name": c.name, "email": c.email,
                "raw_text": c.raw_text, "skills": json.loads(c.skills_json or "[]"),
            } for c in candidates_all]
            jd_dict = {"title": selected_job.title, "description": selected_job.description}
            ranked = rank_candidates(resume_dicts, jd_dict)
            db = get_db()
            for result in ranked:
                cand = next(c for c in candidates_all if c.filename == result["filename"])
                save_scores(db, cand, selected_job, result)
            db.close()
            st.session_state["last_results"] = ranked
            st.session_state["last_job"] = selected_job_title
        st.success(f"✅ Screened {len(ranked)} candidates — results saved.")

    if st.session_state.get("last_results"):
        ranked = st.session_state["last_results"]
        job_label = st.session_state["last_job"]

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">🏆 Ranked Candidates — {job_label}</div>', unsafe_allow_html=True)

        for r in ranked[:10]:
            matched = r.get("matched_skills", [])
            st.markdown(f'''
            <div class="candidate-card">
                {rank_badge(r["rank"])}
                {avatar(r["candidate_name"])}
                <div style="flex:1.5;min-width:130px;">
                    <div style="font-weight:600;color:var(--card-name-color);">{r["candidate_name"]}</div>
                    <div style="font-size:11px;color:var(--card-sub-color);">{r["email"] or "No email"}</div>
                </div>
                {score_bar(r["fit_score"])}
                <div style="flex:1;min-width:120px;">{skill_pills(matched[:4])}</div>
                <div style="display:flex;gap:8px;">
                    <div class="score-chip">
                        <div class="chip-label">TF-IDF</div>
                        <div class="chip-value">{round(r["tfidf_score"]*100)}%</div>
                    </div>
                    <div class="score-chip">
                        <div class="chip-label">Skills</div>
                        <div class="chip-value">{round(r["skill_score"]*100)}%</div>
                    </div>
                    <div class="score-chip">
                        <div class="chip-label">Exp</div>
                        <div class="chip-value">{round(r["experience_score"]*100)}%</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

        df = pd.DataFrame([{
            "Candidate": r["candidate_name"],
            "Fit Score": round(r["fit_score"]*100, 1),
            "TF-IDF": round(r["tfidf_score"]*100, 1),
            "Skill Match": round(r["skill_score"]*100, 1),
            "Experience": round(r["experience_score"]*100, 1),
        } for r in ranked])

        col1, col2 = st.columns(2, gap="large")
        layout_kw = plotly_layout_defaults()

        with col1:
            colors = [fit_color(r["fit_score"]) for r in ranked]
            fig = go.Figure(go.Bar(
                x=df["Fit Score"], y=df["Candidate"],
                orientation="h",
                marker=dict(color=colors, opacity=0.9),
            ))
            fig.update_layout(
                **{**layout_kw, "xaxis": {**layout_kw.get("xaxis", {}), "range": [0, 100], "ticksuffix": "%"},
                   "yaxis": {**layout_kw.get("yaxis", {}), "categoryorder": "total ascending"}},
                title="Overall Fit Score",
                height=max(350, 60*len(ranked))
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if ranked:
                top = ranked[0]
                color = fit_color(top["fit_score"])
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=round(top["fit_score"]*100, 1),
                    number={"suffix": "%", "font": {"size": 40, "color": color}},
                    title={"text": f"🏆 Top: {top['candidate_name']}"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": color, "thickness": 0.24},
                        "bgcolor": "rgba(0,0,0,0)",
                        "steps": [
                            {"range": [0, 45],  "color": "rgba(239,68,68,0.08)"},
                            {"range": [45, 70], "color": "rgba(245,158,11,0.08)"},
                            {"range": [70, 100], "color": "rgba(16,185,129,0.1)"},
                        ],
                    },
                ))
                fig2.update_layout(**layout_kw, height=320)
                st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📋 Full Data Table"):
            st.dataframe(
                df.style.background_gradient(subset=["Fit Score"], cmap="RdYlGn", vmin=0, vmax=100),
                use_container_width=True, hide_index=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CANDIDATE DETAIL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Candidate Detail":
    hero_banner("🔍", "Candidate Deep Dive", "Full profile, skill analysis, and cross-job performance breakdown")

    db = get_db()
    candidates = db.query(Candidate).all()

    if not candidates:
        st.info("ℹ️ No candidates uploaded yet.")
        db.close(); st.stop()

    names = {c.id: (c.name or c.filename) for c in candidates}
    selected_id = st.selectbox(
        "Select candidate",
        list(names.keys()),
        format_func=lambda x: names[x],
        label_visibility="collapsed"
    )
    cand = next(c for c in candidates if c.id == selected_id)
    skills = json.loads(cand.skills_json or "[]")

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        gradients = [
            "linear-gradient(135deg,#6366f1,#8b5cf6)",
            "linear-gradient(135deg,#10b981,#34d399)",
            "linear-gradient(135deg,#8b5cf6,#c084fc)",
            "linear-gradient(135deg,#f59e0b,#fbbf24)",
        ]
        grad = gradients[selected_id % len(gradients)]
        st.markdown(f'''
        <div class="glass-card">
            <div style="text-align:center;margin-bottom:20px;">
                <div style="width:76px;height:76px;border-radius:22px;background:{grad};display:flex;align-items:center;justify-content:center;margin:0 auto 14px;box-shadow:0 8px 24px rgba(99,102,241,0.3);">
                    <span style="font-size:34px;font-weight:800;color:white;">{(cand.name or cand.filename)[0].upper()}</span>
                </div>
                <div style="font-size:19px;font-weight:700;color:var(--card-name-color);">{cand.name or "Unknown"}</div>
                <div style="font-size:11px;color:var(--card-sub-color);">{cand.filename}</div>
            </div>
            <div style="border-top:1px solid var(--border-light);padding-top:14px;">
                <div class="profile-row"><span class="profile-label">Email</span><span class="profile-value">{cand.email or "—"}</span></div>
                <div class="profile-row"><span class="profile-label">Phone</span><span class="profile-value">{cand.phone or "—"}</span></div>
                <div class="profile-row"><span class="profile-label">LinkedIn</span><span class="profile-value">{cand.linkedin or "—"}</span></div>
                <div class="profile-row"><span class="profile-label">Skills</span><span class="profile-value">{len(skills)}</span></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if skills:
            st.markdown('<div class="section-header">🎯 Skills</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="line-height:2.5;">{skill_pills(skills, limit=20)}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">📄 Resume Preview</div>', unsafe_allow_html=True)
        preview = cand.raw_text[:2000] + ("…" if len(cand.raw_text) > 2000 else "")
        st.markdown(
            f'<div style="background:var(--resume-bg);border:1px solid var(--resume-border);border-radius:16px;padding:20px;font-family:monospace;font-size:11px;line-height:1.7;max-height:440px;overflow-y:auto;white-space:pre-wrap;color:var(--resume-text);">{preview}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📊 Performance Across All Jobs</div>', unsafe_allow_html=True)

    scores = db.query(Score).filter_by(candidate_id=cand.id).all()
    jobs_map = {j.id: j.title for j in db.query(JobDescription).all()}
    db.close()

    if scores:
        for s in sorted(scores, key=lambda x: x.fit_score, reverse=True):
            job_title = jobs_map.get(s.job_id, f"Job #{s.job_id}")
            st.markdown(f'''
            <div class="candidate-card" style="margin-bottom:10px;">
                <div style="flex:2;"><strong style="color:var(--card-name-color);">{job_title}</strong></div>
                {score_bar(s.fit_score)}
                <div class="score-chip"><div class="chip-label">TF-IDF</div><div class="chip-value">{round(s.tfidf_score*100)}%</div></div>
                <div class="score-chip"><div class="chip-label">Skills</div><div class="chip-value">{round(s.skill_score*100)}%</div></div>
                <div class="score-chip"><div class="chip-label">Exp</div><div class="chip-value">{round(s.experience_score*100)}%</div></div>
            </div>
            ''', unsafe_allow_html=True)

        score_df = pd.DataFrame([{
            "Job": jobs_map.get(s.job_id, str(s.job_id)),
            "Fit Score": round(s.fit_score*100, 1),
            "TF-IDF": round(s.tfidf_score*100, 1),
            "Skill Match": round(s.skill_score*100, 1),
            "Experience": round(s.experience_score*100, 1),
        } for s in scores]).sort_values("Fit Score", ascending=False)

        fig = go.Figure()
        for col_name, color in [("TF-IDF","#818cf8"), ("Skill Match","#34d399"), ("Experience","#fbbf24")]:
            fig.add_trace(go.Bar(name=col_name, x=score_df["Job"], y=score_df[col_name], marker_color=color))
        fig.update_layout(**plotly_layout_defaults(), barmode="group", title="Score Breakdown by Job", height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No scores yet — run AI screening first.")


# Close main content wrapper
st.markdown('</div>', unsafe_allow_html=True)