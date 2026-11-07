"""Optional local dashboard. Run the CLI first, then: streamlit run app.py"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Kuku Promo Finder", page_icon="🎬", layout="wide")
st.title("🎬 Kuku AI Promo Finder")
st.caption("Local review dashboard for screenplay promo candidates. This dashboard does not upload screenplay data anywhere.")

DEFAULT_RESULT = Path("outputs/latest/promos.json")
source = st.sidebar.text_input("Results JSON path", str(DEFAULT_RESULT))
upload = st.sidebar.file_uploader("Or load a promos.json file", type=["json"])

payload = None
try:
    if upload is not None:
        payload = json.load(upload)
    elif Path(source).exists():
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
except Exception as exc:
    st.error(f"Could not read results: {exc}")

if not payload:
    st.info("Run the command-line pipeline first. See README.md for setup and commands.")
    st.stop()

run_info = payload.get("run", {})
promos = payload.get("promos", [])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Episodes processed", run_info.get("episodes_processed", 0))
col2.metric("Promo candidates", len(promos))
col3.metric("LLM candidates", run_info.get("llm_candidate_count", 0))
col4.metric("Heuristic candidates", run_info.get("heuristic_candidate_count", 0))

if run_info.get("heuristic_candidate_count", 0):
    st.warning("This run contains offline heuristic suggestions. They are not model-generated editorial judgments.")

st.subheader("Ranked promo candidates")
if not promos:
    st.warning("No valid candidates were produced. Check run_report.md and the per-episode errors.")
    st.stop()

frame = pd.DataFrame([
    {
        "Rank": p.get("rank"),
        "Episode": p.get("episode_id"),
        "Start": p.get("segments", [{}])[0].get("start"),
        "End": p.get("segments", [{}])[0].get("end"),
        "Duration (s)": p.get("total_duration_seconds"),
        "Score": p.get("final_score"),
        "Method": p.get("method"),
    }
    for p in promos
])
col_a, col_b = st.columns(2)
with col_a:
    min_score = st.slider("Minimum score", min_value=0, max_value=100, value=0)
with col_b:
    methods = sorted(frame["Method"].dropna().unique().tolist())
    selected_methods = st.multiselect("Method", methods, default=methods)
filtered = frame[(frame["Score"] >= min_score) & (frame["Method"].isin(selected_methods))]
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.subheader("Candidate details")
filtered_ranks = filtered["Rank"].tolist()
if filtered_ranks:
    selected_rank = st.selectbox("Choose a candidate", filtered_ranks)
    selected = next(p for p in promos if p.get("rank") == selected_rank)
    segment = selected.get("segments", [{}])[0]
    st.markdown(f"### Rank #{selected.get('rank')} - Episode {selected.get('episode_id')}")
    st.write(f"**Time:** {segment.get('start')} - {segment.get('end')} ({selected.get('total_duration_seconds')} seconds)")
    st.write(f"**Final score:** {selected.get('final_score')}/100")
    st.write("**Hook**")
    st.write(selected.get("hook", ""))
    st.write("**Cliffhanger**")
    st.write(selected.get("cliffhanger", ""))
    st.write("**Why it works**")
    st.write(selected.get("why_it_works", ""))
    st.write("**Dimension scores**")
    st.json(selected.get("scores", {}))
    st.write("**Evidence excerpts**")
    st.json(selected.get("evidence", {}))
    if selected.get("validation_warnings"):
        st.warning("Review notes: " + " | ".join(selected["validation_warnings"]))
    if selected.get("human_review_required", True):
        st.info("Human editorial review is required before using this clip.")

with st.expander("Run metadata and limitations"):
    st.json(run_info)
