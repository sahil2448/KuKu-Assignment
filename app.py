from __future__ import annotations

import html
import json
from io import StringIO
from typing import Any

import pandas as pd
import io
import zipfile
import streamlit as st
from pathlib import Path


st.set_page_config(
    page_title="Kuku | Promo Finder Studio",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Visual system: cinematic editorial workspace
# -----------------------------------------------------------------------------
CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');

:root {
  --bg: #0c0e12;
  --surface: #141820;
  --surface-2: #1a202a;
  --surface-3: #202733;
  --border: #2a3340;
  --text: #f5f1e9;
  --muted: #a4adba;
  --dim: #737e8c;
  --coral: #ff7058;
  --gold: #f1c879;
  --mint: #8dd9bd;
  --red-soft: #492b2a;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp {
  background:
    radial-gradient(ellipse at 86% 0%, rgba(112, 56, 54, .22), transparent 32%),
    radial-gradient(ellipse at 8% 12%, rgba(110, 83, 50, .11), transparent 26%),
    var(--bg);
  color: var(--text);
}
[data-testid="stHeader"] { background: rgba(12,14,18,.88); }
[data-testid="stToolbar"] { right: 1rem; }
.block-container { max-width: 1480px; padding-top: 2.1rem; padding-bottom: 4rem; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: #11151c;
  border-right: 1px solid #29313c;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.35rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #c3cbd5; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--text); }
.sidebar-brand {
  padding: 1rem 1.05rem; margin-bottom: 1.35rem; border: 1px solid #303844;
  border-radius: 15px; background: linear-gradient(145deg, #211f25, #151a22);
}
.sidebar-brand-mark { display:flex; align-items:center; gap:.65rem; }
.brand-symbol {
  width: 37px; height: 37px; border-radius: 11px; display:grid; place-items:center;
  background: var(--coral); color:#171319; font-weight:900; font-size:1.1rem;
}
.brand-name { color:#fff; font-size:1.05rem; font-weight:800; letter-spacing:-.03em; }
.brand-sub { color:#9ca6b2; font-size:.66rem; text-transform:uppercase; letter-spacing:.16em; margin-top:.12rem; }
.sidebar-label { color:var(--gold); font-size:.67rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; margin:1.15rem 0 .45rem; }

/* General typography and controls */
h1, h2, h3, h4 { color: var(--text) !important; letter-spacing: -.025em; }
p, li, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
small { color: var(--muted); }
hr { border-color: var(--border) !important; }
[data-testid="stMarkdownContainer"] a { color: var(--gold); }
[data-testid="stFileUploader"] {
  background: #171d26; border: 1px dashed #566170; border-radius: 13px; padding: .55rem;
}
[data-testid="stFileUploader"] section { background: transparent; }
[data-testid="stFileUploader"] button {
  border: 1px solid #596676 !important; color: #f4efe6 !important; background:#242d38 !important;
  border-radius: 9px !important;
}
[data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div,
[data-testid="stSlider"] {
  background-color: #171d26; border-color: #384352; border-radius: 10px;
}
[data-baseweb="select"] > div { background:#171d26; border-color:#384352; }
[data-testid="stTextInput"] input { background:#171d26; color:var(--text); border-color:#384352; }
.stButton > button, .stDownloadButton > button {
  border-radius: 10px; border: 1px solid #46515f; background:#222a35; color:#f4efe6;
  font-weight:700; transition:all .18s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color:var(--coral); color:#fff; background:#303845;
}
.stDownloadButton > button[kind="primary"], .stButton > button[kind="primary"] {
  background:var(--coral); color:#1b1515; border-color:var(--coral);
}

/* Hero */
.hero-shell {
  position:relative; overflow:hidden; padding:1.65rem 1.85rem 1.55rem;
  border:1px solid #55413c; border-radius:20px; margin-bottom:1.3rem;
  background:linear-gradient(112deg, #282127 0%, #231d24 52%, #30221f 100%);
  box-shadow:0 18px 55px rgba(0,0,0,.22);
}
.hero-shell:after {
  content:'K'; position:absolute; right:3.6rem; top:-3.9rem; font-family:'Playfair Display',serif;
  font-size:17rem; line-height:1; color:rgba(241,200,121,.055); pointer-events:none;
}
.hero-top { display:flex; align-items:center; gap:.55rem; margin-bottom:.7rem; }
.hero-kicker { color:var(--gold); text-transform:uppercase; letter-spacing:.18em; font-size:.69rem; font-weight:800; }
.hero-dot { width:6px; height:6px; background:var(--coral); border-radius:50%; display:inline-block; }
.hero-title { font-family:'Playfair Display',serif; font-size:2.65rem; line-height:1.1; font-weight:700; color:#fff8ed; letter-spacing:-.035em; margin:0 0 .45rem; }
.hero-subtitle { font-size:.98rem; line-height:1.55; color:#c2b9b3; max-width:780px; margin:0; }
.hero-meta { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.1rem; }
.hero-tag { border:1px solid #62504b; background:rgba(255,255,255,.045); color:#e6dcd2; border-radius:999px; padding:.3rem .65rem; font-size:.69rem; font-weight:700; letter-spacing:.04em; }

/* Section headings */
.section-head { display:flex; align-items:center; gap:.7rem; margin:1.5rem 0 .75rem; }
.section-index { color:var(--coral); font-family:'DM Mono',monospace; font-size:.75rem; font-weight:500; }
.section-title { color:var(--text); font-size:1.18rem; font-weight:800; letter-spacing:-.025em; }
.section-caption { color:var(--dim); font-size:.82rem; margin-top:.15rem; }
.loaded-file { color:#b8c1cc; font-size:.78rem; padding:.5rem .75rem; border-left:2px solid var(--gold); background:#151a22; border-radius:0 8px 8px 0; margin-bottom:1rem; }

/* Metric cards */
.metric-card {
  background:linear-gradient(145deg, #191f28, #141920); border:1px solid #2d3744;
  border-radius:15px; padding:1rem 1.05rem .9rem; min-height:111px;
  box-shadow:0 8px 24px rgba(0,0,0,.12);
}
.metric-label { color:#9ba6b4; text-transform:uppercase; letter-spacing:.105em; font-size:.65rem; font-weight:800; }
.metric-value { color:#fff7eb; font-size:1.9rem; font-weight:800; line-height:1.25; margin-top:.38rem; letter-spacing:-.04em; }
.metric-foot { color:#7f8a98; font-size:.71rem; margin-top:.12rem; }
.metric-accent { color:var(--gold); }
.metric-coral { color:var(--coral); }
.metric-mint { color:var(--mint); }

/* Panels and candidate */
.panel {
  background:#151a22; border:1px solid #2b3541; border-radius:15px; padding:1.15rem 1.25rem;
}
.panel-label { color:var(--gold); font-size:.66rem; font-weight:800; text-transform:uppercase; letter-spacing:.15em; margin-bottom:.55rem; }
.candidate-hero {
  background:linear-gradient(135deg,#1b222c,#171c24); border:1px solid #34404d;
  border-radius:17px; padding:1.25rem 1.35rem; margin:.6rem 0 1rem;
}
.candidate-overline { color:var(--gold); font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.04em; }
.candidate-heading { color:#fff8ed; font-family:'Playfair Display',serif; font-size:1.55rem; line-height:1.25; margin:.42rem 0 .55rem; }
.candidate-meta { color:#aab4c0; font-size:.78rem; }
.pill {
  display:inline-block; padding:.25rem .58rem; border-radius:999px; margin-right:.35rem;
  font-family:'DM Mono',monospace; font-size:.69rem; font-weight:500;
  border:1px solid #4d5968; background:#252e39; color:#e8e2d8;
}
.pill-score { border-color:#805b3a; color:#f4cb84; background:#342920; }
.copy-block { background:#1c232d; border-left:3px solid var(--coral); padding:.8rem .9rem; border-radius:0 10px 10px 0; color:#e8e3da; line-height:1.58; margin:.45rem 0 .9rem; }
.copy-block.gold { border-left-color:var(--gold); }
.copy-block.mint { border-left-color:var(--mint); }
.score-row { display:flex; justify-content:space-between; color:#c4cbd3; font-size:.8rem; margin:.62rem 0 .25rem; }
.score-track { height:6px; background:#303946; border-radius:20px; overflow:hidden; }
.score-fill { height:100%; background:linear-gradient(90deg,var(--coral),var(--gold)); border-radius:20px; }
.warning-panel { background:#2a201d; border:1px solid #744b3f; color:#f2c2ad; border-radius:12px; padding:.85rem 1rem; }
.success-panel { background:#182822; border:1px solid #315e4e; color:#b6e4d0; border-radius:12px; padding:.85rem 1rem; }
.note-panel { background:#1b222b; border:1px solid #394554; color:#bdc8d2; border-radius:12px; padding:.85rem 1rem; }

/* Dataframe */
[data-testid="stDataFrame"] { border:1px solid #303b48; border-radius:12px; overflow:hidden; }
[data-testid="stDataFrame"] iframe { background:#171d26; }

/* Expander, alert, progress */
[data-testid="stExpander"] { background:#151a22; border:1px solid #2c3642; border-radius:12px; }
[data-testid="stAlert"] { border-radius:12px; }
.stProgress > div > div > div > div { background:linear-gradient(90deg,var(--coral),var(--gold)); }

/* Footer */
.footer-line { border-top:1px solid #2a333f; margin-top:2rem; padding-top:.9rem; color:#788391; font-size:.72rem; display:flex; justify-content:space-between; gap:1rem; }
@media (max-width: 800px) {
  .block-container { padding-top:1rem; }
  .hero-shell { padding:1.2rem; }
  .hero-title { font-size:2rem; }
  .hero-shell:after { right:-1.4rem; font-size:11rem; }
  .metric-card { min-height:96px; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def section_heading(index: str, title: str, caption: str = "") -> None:
    caption_html = f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    st.markdown(
        f'<div class="section-head"><span class="section-index">{html.escape(index)}</span>'
        f'<div><div class="section-title">{html.escape(title)}</div>{caption_html}</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, foot: str, accent: str = "") -> None:
    accent_class = f" metric-{accent}" if accent else ""
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value{accent_class}">{html.escape(value)}</div>'
        f'<div class="metric-foot">{html.escape(foot)}</div></div>',
        unsafe_allow_html=True,
    )


def _normalise_json(payload: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        raise ValueError("The JSON file must contain an object with a 'promos' list.")
    rows = payload.get("promos")
    if not isinstance(rows, list):
        raise ValueError("No 'promos' list was found in the JSON file.")
    clean_rows: list[dict[str, Any]] = []
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            continue
        segments = item.get("segments") or [{}]
        segment = segments[0] if isinstance(segments[0], dict) else {}
        evidence = item.get("evidence") or {}
        if not isinstance(evidence, dict):
            evidence = {}
        clean_rows.append(
            {
                "rank": item.get("rank", index),
                "promo_id": item.get("promo_id", f"P{index:03d}"),
                "episode_id": item.get("episode_id", segment.get("episode_id", "")),
                "start": segment.get("start", item.get("start", "")),
                "end": segment.get("end", item.get("end", "")),
                "duration_seconds": item.get("total_duration_seconds", segment.get("duration_seconds", 0)),
                "hook": item.get("hook", ""),
                "cliffhanger": item.get("cliffhanger", ""),
                "why_it_works": item.get("why_it_works", ""),
                "hook_evidence": evidence.get("hook", item.get("hook_evidence", "")),
                "cliffhanger_evidence": evidence.get("cliffhanger", item.get("cliffhanger_evidence", "")),
                "scores": item.get("scores") or {},
                "final_score": item.get("final_score", 0),
                "method": item.get("method", ""),
                "validation_warnings": item.get("validation_warnings") or [],
                "human_review_required": item.get("human_review_required", True),
            }
        )
    return payload.get("run", {}) or {}, clean_rows


def _normalise_csv(text: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    frame = pd.read_csv(StringIO(text)).fillna("")
    required = {"episode_id", "start", "end", "final_score"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(sorted(missing)))
    rows: list[dict[str, Any]] = []
    for index, row in frame.iterrows():
        warnings_value = str(row.get("validation_warnings", "")).strip()
        rows.append(
            {
                "rank": row.get("rank", index + 1),
                "promo_id": row.get("promo_id", f"P{index + 1:03d}"),
                "episode_id": row.get("episode_id", ""),
                "start": row.get("start", ""),
                "end": row.get("end", ""),
                "duration_seconds": row.get("duration_seconds", 0),
                "hook": row.get("hook", ""),
                "cliffhanger": row.get("cliffhanger", ""),
                "why_it_works": row.get("why_it_works", ""),
                "hook_evidence": "",
                "cliffhanger_evidence": "",
                "scores": {
                    "hook": row.get("hook_score", ""),
                    "cliffhanger": row.get("cliffhanger_score", ""),
                    "standalone_clarity": row.get("standalone_clarity_score", ""),
                    "emotional_intensity": row.get("emotional_intensity_score", ""),
                },
                "final_score": row.get("final_score", 0),
                "method": row.get("method", ""),
                "validation_warnings": [x.strip() for x in warnings_value.split("|") if x.strip()],
                "human_review_required": True,
            }
        )
    return {}, rows


# -----------------------------------------------------------------------------
# Brand and sidebar
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
      <div class="sidebar-brand-mark">
        <div class="brand-symbol">K</div>
        <div><div class="brand-name">KUKU</div><div class="brand-sub">Promo Finder Studio</div></div>
      </div>
    </div>
    <div class="sidebar-label">01 / Load your run</div>
    """,
    unsafe_allow_html=True,
)
uploaded = st.sidebar.file_uploader(
        "Upload promotional results (JSON or ZIP)",

    type=["json", "csv","zip"],
    help="Upload promos.json for run metadata and evidence fields, or promos.csv for a compact ranked view.",
)
st.sidebar.markdown('<div class="sidebar-label">02 / Review controls</div>', unsafe_allow_html=True)
st.sidebar.caption("Filters appear in the main workspace after a results file is loaded.")
st.sidebar.divider()
st.sidebar.markdown(
    "<div class='sidebar-label'>PIPELINE</div>", unsafe_allow_html=True
)
st.sidebar.markdown(
    "**MODEL**\n\nQwen 3.8 27B\n\n**PROVIDER**\n\nGroq\n\n**METHOD**\n\nScript parsing · AI suggestions · rule-based validation",
)
st.sidebar.divider()
st.sidebar.markdown(
    "<div class='small-muted'>Built for editorial discovery.<br>Human approval remains essential.</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "[Source repository ↗](https://github.com/sahil2448/KuKu-Assignment)",
)


# -----------------------------------------------------------------------------
# Main header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-shell">
      <div class="hero-top"><span class="hero-dot"></span><span class="hero-kicker">Microdrama / Editorial intelligence</span></div>
      <div class="hero-title">Find the moment.<br>Make them need the next one.</div>
      <p class="hero-subtitle">A screening workspace for AI-suggested promotional moments across timestamped microdrama episodes. Explore the shortlist, inspect the story beat, and decide what deserves an editor’s attention.</p>
      <div class="hero-meta">
        <span class="hero-tag">20–60 SEC PROMOS</span>
        <span class="hero-tag">HOOK → CLIFFHANGER</span>
        <span class="hero-tag">HUMAN-IN-THE-LOOP REVIEW</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if uploaded is None:
    section_heading("01", "Start with a results file", "The hosted demo reviews outputs; it does not run generation or need an API key.")
    empty_cols = st.columns([1.1, 1, 1])
    with empty_cols[0]:
        st.markdown(
            """
            <div class="panel" style="min-height:190px">
              <div class="panel-label">Recommended file</div>
              <h3 style="margin:.1rem 0 .55rem;color:#fff8ed">promos.json</h3>
              <p style="line-height:1.6">Upload the JSON output from your CLI run to see candidate evidence, scoring details, episode metadata and validation notes.</p>
              <span class="pill pill-score">Full-detail view</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with empty_cols[1]:
        st.markdown(
            """
            <div class="panel" style="min-height:190px">
              <div class="panel-label">01 / Discover</div>
              <h3 style="margin:.1rem 0 .55rem;color:#fff8ed">Ranked shortlist</h3>
              <p style="line-height:1.6">Compare suggestions by episode, duration, score and automated validation status.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with empty_cols[2]:
        st.markdown(
            """
            <div class="panel" style="min-height:190px">
              <div class="panel-label">02 / Inspect</div>
              <h3 style="margin:.1rem 0 .55rem;color:#fff8ed">Editorial review</h3>
              <p style="line-height:1.6">Inspect the hook, cliffhanger, rationale, evidence excerpts and score breakdown before selection.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="note-panel"><b style="color:#f1c879">Privacy note</b><br>Do not upload the original screenplay ZIP. Upload only generated results that you are authorised to share with this hosted service. The dashboard does not require your Groq API key.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="footer-line"><span>KUKU PROMO FINDER · REVIEW STUDIO</span><span>AI shortlist ≠ publication approval</span></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# -----------------------------------------------------------------------------
# Load and normalise results
# -----------------------------------------------------------------------------
try:
    filename = uploaded.name.lower()

    if filename.endswith(".zip"):

        zip_bytes = uploaded.getvalue()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:

            json_files = [
                name for name in archive.namelist()
                if name.replace("\\", "/").rsplit("/", 1)[-1].lower()
                == "promos.json"
            ]

            if not json_files:
                st.error("ZIP does not contain promos.json")
                st.stop()

            # Read JSON while the ZIP archive is still open
            json_bytes = archive.read(json_files[0])

        # Parse after reading the bytes into memory
        payload = json.loads(json_bytes.decode("utf-8-sig"))

        run_info, promos = _normalise_json(payload)
        source_type = "ZIP · full-detail JSON results"

    elif filename.endswith(".json"):

        raw = uploaded.getvalue().decode("utf-8-sig")
        payload = json.loads(raw)

        run_info, promos = _normalise_json(payload)
        source_type = "JSON · full-detail results"

    elif filename.endswith(".csv"):

        raw = uploaded.getvalue().decode("utf-8-sig")

        run_info, promos = _normalise_csv(raw)
        source_type = "CSV · evidence fields are not included"

    else:
        st.error("Unsupported file format.")
        st.stop()

except Exception as exc:
    st.error(f"Could not load this file: {exc}")
    st.stop()

if not promos:
    st.warning("The uploaded file contains no promotional candidates.")
    st.stop()

for row in promos:
    try:
        row["final_score"] = float(row.get("final_score") or 0)
        row["episode_id"] = int(float(row.get("episode_id")))
        row["duration_seconds"] = float(row.get("duration_seconds") or 0)
        row["rank"] = int(float(row.get("rank") or 0))
    except (TypeError, ValueError):
        pass
    if not isinstance(row.get("validation_warnings"), list):
        row["validation_warnings"] = []

promos.sort(
    key=lambda item: (float(item.get("final_score") or 0), -int(item.get("rank") or 999999)),
    reverse=True,
)
episodes = sorted({p.get("episode_id") for p in promos if p.get("episode_id") not in (None, "")})
no_warning_count = sum(not p.get("validation_warnings") for p in promos)
avg_score = sum(float(p.get("final_score") or 0) for p in promos) / len(promos)

st.markdown(
    f'<div class="loaded-file">LOADED · {html.escape(uploaded.name)} &nbsp; / &nbsp; {html.escape(source_type)}</div>',
    unsafe_allow_html=True,
)
section_heading("02", "Run at a glance", "A quick read of the current candidate set.")
metric_cols = st.columns(4)
with metric_cols[0]:
    metric_card("Promo candidates", str(len(promos)), "AI-generated suggestions", "coral")
with metric_cols[1]:
    metric_card("Episodes represented", str(len(episodes)), "Episodes with at least one candidate", "gold")
with metric_cols[2]:
    metric_card("No warning flags", str(no_warning_count), "Passed automated checks only", "mint")
with metric_cols[3]:
    metric_card("Average score", f"{avg_score:.1f}", "Out of 100 · model-assigned", "gold")

if run_info:
    meta_cols = st.columns(4)
    metadata = [
        ("Episodes processed", run_info.get("episodes_processed", "—")),
        ("Processing errors", run_info.get("episodes_with_errors", "—")),
        ("AI provider", run_info.get("llm_provider", "—")),
        ("Model", run_info.get("llm_model", "—")),
    ]
    for col, (label, value) in zip(meta_cols, metadata):
        with col:
            st.markdown(
                f'<div class="metric-card" style="min-height:77px;padding:.72rem .9rem">'
                f'<div class="metric-label">{html.escape(str(label))}</div>'
                f'<div style="color:#e8e2d8;font-size:.91rem;font-weight:700;margin-top:.45rem">{html.escape(str(value))}</div></div>',
                unsafe_allow_html=True,
            )

# -----------------------------------------------------------------------------
# Filters and ranked table
# -----------------------------------------------------------------------------
section_heading("03", "Explore the shortlist", "Narrow the list, then open a candidate for a closer read.")
filter_cols = st.columns([1, 1.25, 1.45])
with filter_cols[0]:
    min_score = st.slider("Minimum score", 0, 100, 0, 1)
with filter_cols[1]:
    selected_episodes = st.multiselect("Episodes", episodes, default=episodes)
with filter_cols[2]:
    warning_filter = st.selectbox(
        "Automated validation",
        ["All candidates", "No warnings", "Warnings present"],
    )

filtered = [
    p for p in promos
    if float(p.get("final_score") or 0) >= min_score
    and p.get("episode_id") in selected_episodes
    and (
        warning_filter == "All candidates"
        or (warning_filter == "No warnings" and not p.get("validation_warnings"))
        or (warning_filter == "Warnings present" and bool(p.get("validation_warnings")))
    )
]

if not filtered:
    st.info("No candidates match these filters. Adjust the score or episode selection.")
    st.stop()

summary = pd.DataFrame(
    [
        {
            "Rank": p.get("rank"),
            "Episode": p.get("episode_id"),
            "Start": p.get("start"),
            "End": p.get("end"),
            "Duration": round(float(p.get("duration_seconds") or 0), 1),
            "Score": round(float(p.get("final_score") or 0), 1),
            "Flags": len(p.get("validation_warnings", [])),
        }
        for p in filtered
    ]
)
left, right = st.columns([1.45, .55])
with left:
    st.dataframe(summary, use_container_width=True, hide_index=True, height=min(430, 44 + 36 * len(summary)))
with right:
    st.markdown(
        f'<div class="panel"><div class="panel-label">Current view</div>'
        f'<div style="font-family:Playfair Display,serif;color:#fff8ed;font-size:2rem">{len(filtered):02d}</div>'
        f'<div style="color:#a4adba;font-size:.8rem">candidates match your filters</div>'
        f'<hr style="border-color:#303a46">'
        f'<div style="color:#f1c879;font-size:.7rem;font-weight:800;letter-spacing:.12em">EXPORT</div>'
        f'<p style="font-size:.8rem;line-height:1.5">Download this filtered view for a focused editorial pass.</p></div>',
        unsafe_allow_html=True,
    )
    csv_bytes = summary.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download shortlist CSV",
        data=csv_bytes,
        file_name="kuku_filtered_promo_shortlist.csv",
        mime="text/csv",
        use_container_width=True,
    )

# -----------------------------------------------------------------------------
# Candidate inspector
# -----------------------------------------------------------------------------
section_heading("04", "Candidate inspector", "Read the story beat and inspect the model's scoring rationale.")
choices = {
    f"#{p.get('rank')}  ·  EP {p.get('episode_id')}  ·  {p.get('start')}–{p.get('end')}  ·  {p.get('final_score')}/100": p
    for p in filtered
}
selected_label = st.selectbox("Choose a candidate", list(choices.keys()))
selected = choices[selected_label]

st.markdown(
    f'<div class="candidate-hero"><div class="candidate-overline">EPISODE {html.escape(str(selected.get("episode_id")))} &nbsp; / &nbsp; PROMO #{html.escape(str(selected.get("rank")))}</div>'
    f'<div class="candidate-heading">A moment worth stopping for.</div>'
    f'<div class="candidate-meta">{html.escape(str(selected.get("start")))} → {html.escape(str(selected.get("end")))} &nbsp; · &nbsp; {float(selected.get("duration_seconds") or 0):.1f} seconds</div>'
    f'<div style="margin-top:.8rem"><span class="pill">20–60 SEC FORMAT</span><span class="pill pill-score">{float(selected.get("final_score") or 0):.1f} / 100</span>'
    f'<span class="pill">{len(selected.get("validation_warnings", []))} VALIDATION FLAGS</span></div></div>',
    unsafe_allow_html=True,
)

content_col, score_col = st.columns([1.35, .85], gap="large")
with content_col:
    st.markdown('<div class="panel-label">01 / Opening hook</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="copy-block">{html.escape(str(selected.get("hook") or "Not provided"))}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">02 / Cliffhanger ending</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="copy-block gold">{html.escape(str(selected.get("cliffhanger") or "Not provided"))}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">03 / Why this works</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="copy-block mint">{html.escape(str(selected.get("why_it_works") or "Not provided"))}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Evidence excerpts</div>', unsafe_allow_html=True)
    evidence_a, evidence_b = st.columns(2)
    with evidence_a:
        st.caption("HOOK EVIDENCE")
        st.write(selected.get("hook_evidence") or "Not supplied in model output")
    with evidence_b:
        st.caption("CLIFFHANGER EVIDENCE")
        st.write(selected.get("cliffhanger_evidence") or "Not supplied in model output")

with score_col:
    scores = selected.get("scores") or {}
    score_labels = [
        ("Hook strength", "hook"),
        ("Cliffhanger", "cliffhanger"),
        ("Standalone clarity", "standalone_clarity"),
        ("Emotional intensity", "emotional_intensity"),
    ]
    score_parts = []
    for label, key in score_labels:
        value = scores.get(key)
        try:
            numeric = max(0, min(5, float(value)))
        except (TypeError, ValueError):
            numeric = 0
        display_value = f"{numeric:g}/5" if value not in (None, "") else "—"
        score_parts.append(
            f'<div class="score-row"><span>{html.escape(label)}</span>'
            f'<b style="color:#f4d69c">{display_value}</b></div>'
            f'<div class="score-track"><div class="score-fill" style="width:{numeric / 5 * 100:.1f}%"></div></div>'
        )

    warnings = selected.get("validation_warnings") or []
    if warnings:
        warning_html = "".join(f"<li>{html.escape(str(w))}</li>" for w in warnings)
        status_html = (
            f'<div class="warning-panel"><b>Review flags</b>'
            f'<ul style="margin:.45rem 0 0;padding-left:1.1rem">{warning_html}</ul></div>'
        )
    else:
        status_html = (
            '<div class="success-panel"><b>No automated warning flags</b>'
            '<br><span style="font-size:.78rem">Still requires editorial review.</span></div>'
        )

    human_html = (
        '<div class="note-panel" style="margin-top:.8rem"><b>Human review required</b>'
        '<br><span style="font-size:.78rem">Check the source screenplay and final video before approving this promo.</span></div>'
        if selected.get("human_review_required", True) else ""
    )
    st.markdown(
        '<div class="panel"><div class="panel-label">Score breakdown</div>'
        + "".join(score_parts)
        + '<div style="height:.9rem"></div>'
        + status_html
        + human_html
        + '</div>',
        unsafe_allow_html=True,
    )

if run_info:
    with st.expander("Run metadata and project limitations"):
        st.json(run_info)

st.markdown(
    '<div class="footer-line"><span>KUKU PROMO FINDER · EDITORIAL REVIEW STUDIO</span><span>AI-generated shortlist · Human approval required</span></div>',
    unsafe_allow_html=True,
)
