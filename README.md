# Kuku AI Promo Finder

A local Python tool that reads timestamped microdrama screenplays, proposes 20-60 second promotional clips, validates timestamps and duration, scores candidates, and ranks suggestions across the supplied episodes.

This project was built around the supplied **I Married a Broken Soldier. He was a Duke** screenplay pack. The pack contains 50 `.txt` scripts with episode loglines, continuity notes, scene start/end times, and timed camera, action, sound-effect, and dialogue blocks.

## What it does

1. Reads a screenplay ZIP directly (without extracting untrusted ZIP paths) or a folder of `.txt` scripts.
2. Parses episode metadata, scenes, and individual timed screenplay blocks.
3. Sends one episode per request to OpenRouter, asking for up to three promo candidates with hook, cliffhanger, explanation, evidence excerpts, and four 1-5 scores.
4. Validates candidate timestamps, episode boundaries, and the required 20-60 second duration.
5. Calculates a transparent weighted score and ranks candidates.
6. Saves exact raw model responses separately from cleaned/validated output.
7. Provides an offline heuristic mode for technical testing without an API key.

The tool recommends promo moments only. It does not edit, render, or export video clips.

## Important scope choices

- **One continuous segment per promo in version 1.** The assignment also allows montages from multiple moments. This first version focuses on one continuous segment per candidate; the output `segments` array can be extended later.
- **One episode per AI request.** Episode loglines and continuity notes are included, with adjacent episode loglines as context. Candidates from all episodes are ranked together.
- **Human review is required.** A screenplay cannot prove acting, camera performance, edit rhythm, music, or whether a final video works visually.
- **Scores are prioritization aids.** Initial weights are assumptions: hook 30%, cliffhanger 30%, standalone clarity 25%, emotional intensity 15%.
- **Heuristic mode is not an AI result.** It is a deterministic baseline for checking parsing, timestamps, exports, and the dashboard.

## Requirements

- Python 3.10 or later (Python 3.11 recommended).
- Internet access for OpenRouter AI mode.
- An OpenRouter API key.

## Windows / Git Bash setup

Run commands from the `kuku_promo_finder` project folder. Activate your existing virtual environment first if it is not already active.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Put the supplied screenplay ZIP in `data/`:

```text
kuku_promo_finder/
  data/
    I Married a Broken Soldier. He was a Duke-scripts.zip
```

Do not commit the input pack to a public GitHub repository. `data/`, `.zip` files, `outputs/`, `.env`, and `.venv/` are excluded by `.gitignore`.

## Configure OpenRouter

1. Create an API key at <https://openrouter.ai/settings/keys>.
2. Copy `.env.example` to `.env` in this project root.
3. Add the key and model:

```text
OPENROUTER_API_KEY=your_real_key_here
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```

Never share your API key or commit `.env`.

### Confidentiality and provider filtering

Kuku says the screenplay pack is confidential and must not be published or shared. OpenRouter forwards API inputs to the selected model provider; providers have their own data practices. This project therefore includes `provider.data_collection = deny` in every API request. OpenRouter documents this as restricting routing to providers that do not collect user data. If no eligible provider is available, the request should fail instead of routing to a less private provider. This is a safeguard, not a guarantee that third-party processing is equivalent to local processing. Review Kuku's permission and OpenRouter/provider terms before sending the scripts. See <https://openrouter.ai/settings/privacy> and <https://openrouter.ai/docs/guides/privacy/provider-logging>.

The default model is **Google Gemma 4 31B (free)** (`google/gemma-4-31b-it:free`). It has a 262K-token context window and supports JSON output on OpenRouter. Free model availability, providers, and limits can change. The project asks for JSON mode and validates the returned structure locally.

## Run the AI test and full 50-episode batch

OpenRouter currently limits free `:free` model variants to 50 requests per day for accounts below the applicable credit threshold, and failed requests count toward the limit. This pipeline makes one request per episode. To fit the one-episode test inside the same 50-request daily allowance, run the test in the final output folder, then resume that same folder for the remaining episodes.

### 1. Test only Episode 1

```bash
python -m kukupromo --input "data/I Married a Broken Soldier. He was a Duke-scripts.zip" --mode ai --limit 1 --top-per-episode 3 --delay 3.2 --out "outputs/openrouter_full"
```

Check that `outputs/openrouter_full/raw_responses/episode_001.txt` exists and inspect `run_report.md`. This first successful episode is saved as a checkpoint.

### 2. Process all 50 episodes and reuse Episode 1

```bash
python -m kukupromo --input "data/I Married a Broken Soldier. He was a Duke-scripts.zip" --mode ai --top-per-episode 3 --delay 3.2 --out "outputs/openrouter_full" --resume
```

The `--resume` flag loads completed episode checkpoints, so a successful Episode 1 test is not requested again. The remaining 49 episodes each use one API request. If any request fails, it is saved under `errors/`; failed calls may still count toward the free daily limit. Retry failed episodes after the quota resets, or use a paid model/provider if permitted. Do not change the input/model while reusing the same checkpoint folder.

### Modes

- `--mode ai`: OpenRouter only. An API error is recorded; no heuristic replacement is made.
- `--mode heuristic`: local baseline only. No external model call.
- `--mode auto`: uses OpenRouter when the key exists; if an episode request fails, it explicitly labels that episode's fallback as heuristic.

For a genuine AI submission, prefer `--mode ai` and verify the method labels are `openrouter_llm`, not `heuristic_offline`.

## Resume after interruption

The tool writes an episode checkpoint after each processed episode. Resume using the same model, input and output path:

```bash
python -m kukupromo --input "data/I Married a Broken Soldier. He was a Duke-scripts.zip" --mode ai --out "outputs/openrouter_full" --resume
```

Error checkpoints are not treated as completed, so they are retried. This can use additional free requests. Checkpoints are not tied to an input-file hash; use a new output folder if changing the input or model.

## Outputs

```text
outputs/openrouter_full/
  promos.json                 # Complete structured ranked results + run metadata
  promos.csv                  # Spreadsheet-friendly ranked results
  run_report.json             # Counts, model, score weights and per-episode status
  run_report.md               # Human-readable run report
  quality_review_template.csv # Blank human QA columns for the top 30 candidates
  raw_responses/               # Exact, unedited model response text
  checkpoints/                 # Per-episode processed candidate checkpoints
  errors/                      # Per-episode API/parse errors
  heuristic_outputs/           # Explicitly labelled heuristic results, if used
```

Keep raw model responses unedited for submission. They can contain excerpts from the confidential screenplay, so share them only through the Kuku submission form or another channel Kuku has approved. Never publish the screenplay pack, `.env`, or raw responses in a public repository.

## Scoring

Each candidate receives four scores from 1 to 5:

| Dimension | Weight |
|---|---:|
| Hook in first 3 seconds | 30% |
| Cliffhanger at the end | 30% |
| Standalone clarity | 25% |
| Emotional intensity | 15% |

The final score is calculated in Python:

```text
final_score = (30*hook + 30*cliffhanger + 25*standalone_clarity + 15*emotional_intensity) / 5
```

This creates a 20-100 scale. Scores are model/editorial estimates, not measured audience performance.

## Quality checks before submitting

1. Run all 50 episodes in AI mode and inspect `run_report.md` and `run_report.json`.
2. Check that all expected episodes are processed and disclose any errors or zero-candidate episodes.
3. Open `promos.csv` and inspect the top recommendations.
4. For the top 10-15, compare each timestamp with the actual episode video, especially the first three seconds and final cliffhanger. If video access is unavailable, state that review was screenplay-only.
5. Fill `quality_review_template.csv` with approvals and specific failure reasons. Do not claim video checks you did not perform.
6. Record at least one real failure only if it occurred; do not invent a failure example.
7. Keep the screenplay ZIP, `.env`, and raw output folder out of public GitHub.

## Optional local dashboard

The dashboard only views generated results; it does not send screenplay data to Streamlit. Install the UI requirements and launch it:

```bash
python -m pip install -r requirements-ui.txt
streamlit run app.py
```

Load `outputs/openrouter_full/promos.json` in the sidebar.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Design notes for the interview

- Python handles parsing, timestamps, duration checks, evidence checks, score calculation, ranking, deduplication, and exports.
- OpenRouter's selected model judges the dramatic hook, unresolved ending, standalone clarity, and emotional potential.
- The provider/model is configurable through `.env` and `--model`.
- The first version uses one continuous segment per candidate. A future version could add 2-4 segment montages across episodes.

## Troubleshooting

- **`OPENROUTER_API_KEY is not set`:** check the `.env` file is in the project root and the variable name is exact.
- **401:** check the key in OpenRouter and create a new key if needed. Never paste it into chat or GitHub.
- **402:** model/provider requires credits or the account has no available balance.
- **403 / provider policy error:** the request was blocked by the `data_collection=deny` requirement or provider access. Do not remove the privacy restriction just to force the request through on confidential content; review account privacy/provider settings or use an approved provider.
- **429:** free-tier rate or daily request limit. Wait for reset; failed requests may count.
- **5xx / timeout:** provider availability issue. Inspect `errors/`; rerun with `--resume` after the provider recovers.
- **No valid AI candidates:** inspect the raw response and episode error. Do not force recommendations if model output fails validation.
- **Timestamp warnings:** compare the suggested times with source screenplay events; timestamps use `MM:SS.ss`.
