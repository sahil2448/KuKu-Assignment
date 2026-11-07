# Kuku Promo Finder — Streamlit Review Studio

A results-review dashboard for the Kuku microdrama promo-finding prototype. It reads the CLI-generated `promos.json` or `promos.csv`, shows summary metrics, filters the ranked candidates, and exposes each candidate's hook, cliffhanger, rationale, score breakdown and validation flags.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Upload `outputs/groq_final_run/promos.json` in the sidebar. JSON is recommended because it contains run metadata and evidence fields that a CSV may omit.

## Deploy

Deploy this repository on [Streamlit Community Cloud](https://share.streamlit.io/), using `app.py` as the main file. The `.streamlit/config.toml` file applies the dark editorial theme.

## Privacy

This dashboard does not call Groq and does not need the Groq API key. It displays only results files uploaded by the reviewer. Do not upload the original screenplay ZIP or any material you are not authorised to share with the hosting service. The source screenplay pack and generated raw outputs should remain private unless Kuku's submission channel specifically requests them.

## Scope and limitations

The dashboard is a review interface, not the generation pipeline. AI generation runs through the reusable Python CLI in `kukupromo/`. Model scores and automated validation flags are prioritisation aids, not proof that a promo is publication-ready. Human editorial review is required.
