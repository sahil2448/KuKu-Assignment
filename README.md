# Kuku Promo Finder

**An AI-assisted tool for finding and ranking promotional moments in microdrama screenplays.**

This repository contains the screenplay-processing pipeline and a Streamlit review interface built for **Problem 1 — Find the Promos (Ads)** in the Kuku AI Generalist Assignment.

The prototype reads timestamped screenplay text, proposes short promotional clips, checks the suggestions against screenplay timing and evidence, ranks the remaining candidates, and lets a reviewer inspect the results.

> **Important:** This is a decision-support tool for editors. It does not edit video and does not approve clips for publication. Every recommendation needs human review.

---

## 1. Problem and scope

An editor currently has to watch episodes and find 20–60-second moments that could work as ads on platforms such as Instagram, TikTok and YouTube. A useful promo should:

- **Open with a hook:** something attention-grabbing in the first three seconds.
- **End on an unresolved moment:** it should create a reason to watch what happens next.
- **Stand on its own:** a new viewer should understand the basic situation without knowing the series.
- **Use real moments from the episode:** the suggested timestamps and supporting details must come from the supplied screenplay.

The first version focuses on one continuous segment from one episode per candidate. It ranks candidates across the supplied episodes; it does not create multi-segment edits or combine scenes across episodes.

## 2. How it works

The pipeline separates deterministic processing from model judgement:

1. **Read the input.** The parser accepts a ZIP archive of `.txt` screenplays or a directory containing `.txt` files.
2. **Extract timed material.** It reads episode metadata, scene headings, scene boundaries, and timestamped dialogue, action, camera and sound blocks.
3. **Build an episode prompt.** The model receives one episode's scenes and timed events. Adjacent episode loglines may be included as continuity context; their timestamps are not used for the current episode.
4. **Generate candidates.** Groq's OpenAI-compatible API is called with the configured model. The prompt requests up to the configured number of 20–60-second continuous clips, each with a hook, cliffhanger, rationale, evidence excerpts and four scores.
5. **Validate and rank.** Python parses the response, rejects structurally invalid candidates, adds warnings for timing/evidence issues, computes a weighted score and removes heavily overlapping suggestions within an episode.
6. **Save results.** Per-episode checkpoints allow a run to resume after an interruption. JSON, CSV and run reports are written to the output directory.
7. **Review in the dashboard.** The Streamlit app loads generated results so a person can filter, compare and inspect candidates.

### Scoring

The model rates each dimension from **1 (weak) to 5 (excellent)**. The final score is a weighted score out of 100:

| Dimension | Weight |
|---|---:|
| Hook | 30% |
| Cliffhanger | 30% |
| Standalone clarity | 25% |
| Emotional intensity | 15% |

The score is a ranking aid, not a measured prediction of views, watch-through rate or conversion. Validation warnings are displayed separately; a high score does not override a warning.

## 3. Repository layout

```text
kuku_promo_finder/
├── app.py                     # Streamlit results-review dashboard
├── .streamlit/config.toml     # Dashboard theme configuration
├── kukupromo/
│   ├── cli.py                 # Command-line entry point and run orchestration
│   ├── parser.py              # ZIP/folder screenplay parser
│   ├── prompts.py             # Model prompt and response validation
│   ├── groq.py                # Groq model adapter
│   ├── models.py              # Episode/candidate data models and scoring
│   ├── output.py              # JSON, CSV and report generation
│   └── heuristics.py          # Offline heuristic baseline
├── tests/                     # Automated tests
├── docs/                      # Quality-review notes and supporting documents
├── requirements.txt           # Core CLI dependencies
├── requirements-ui.txt        # Core dependencies plus Streamlit dashboard packages
├── pyproject.toml             # Package metadata and CLI entry point
└── .env.example               # Safe example environment configuration
```

The original Kuku screenplay pack, actual `.env` file and generated run outputs are intentionally not part of the public source repository. Keep assignment input material and raw outputs in the location requested by Kuku's submission process.

## 4. Requirements and local setup

- Python **3.10 or newer**.
- A Groq API key for AI mode.
- The screenplay input pack in the supported timestamped `.txt` format, either as a ZIP or a folder of text files.

### Create an environment

From the repository root:

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-ui.txt
```

**macOS / Linux / Git Bash:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-ui.txt
```

`requirements-ui.txt` installs the core dependencies as well as Streamlit and pandas, so it is suitable for running both the CLI and the review dashboard.

### Configure the API key

Copy `.env.example` to `.env` and add your own key:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

The CLI reads the key locally. **Never commit `.env`, paste an API key into source code, or include a key in screenshots or recordings.** The dashboard itself only reviews generated files and does not call Groq, so a reviewer does not need your API key to use the dashboard.

## 5. Run the screenplay pipeline

Place an authorised screenplay ZIP or a directory of screenplay `.txt` files somewhere local. Do not add Kuku's confidential input pack to GitHub.

Example AI run:

```bash
python -m kukupromo \
  --input "path/to/screenplays.zip" \
  --mode ai \
  --model qwen/qwen3.8-27b \
  --top-per-episode 3 \
  --delay 60 \
  --resume \
  --out "outputs/my_run"
```

On Windows PowerShell, the same command can be entered on one line:

```powershell
python -m kukupromo --input "path/to/screenplays.zip" --mode ai --model qwen/qwen3.8-27b --top-per-episode 3 --delay 60 --resume --out "outputs/my_run"
```

Useful options:

| Option | Purpose |
|---|---|
| `--input` | Required ZIP archive or folder of screenplay `.txt` files. |
| `--out` | Output directory; defaults to `outputs/latest`. |
| `--mode ai` | Require the Groq model. API errors are reported; there is no heuristic fallback in this mode. |
| `--mode auto` | Use Groq when configured and fall back to the offline heuristic baseline when AI is unavailable. |
| `--mode heuristic` | Run the offline heuristic baseline without an LLM. These suggestions are not model-generated editorial judgements. |
| `--model` | Groq model ID. Defaults to `GROQ_MODEL` or `qwen/qwen3.8-27b`. |
| `--top-per-episode` | Maximum number of candidates retained per episode; default is 3. |
| `--limit` | Process only the first N episodes, useful for a small test run. |
| `--delay` | Seconds between model requests. Adjust to the limits of the selected provider/model. A delay controls request pacing; it does not increase a daily token allowance. |
| `--resume` | Reuse successfully processed episode checkpoints in the output directory. |
| `--env-file` | Path to the local environment file; defaults to `.env`. |

For a quick parser/pipeline smoke test without using an API, run a small heuristic test:

```bash
python -m kukupromo --input "path/to/screenplays.zip" --mode heuristic --limit 2 --out "outputs/smoke_test"
```

The offline heuristic mode is a baseline for testing the pipeline. Do not combine its output with LLM output without clearly identifying the method used.

## 6. Run the Streamlit review dashboard

From the repository root, with the environment activated:

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

The dashboard is a **review interface**, not the generation pipeline. Upload one of the generated result files:

- `promos.json` — recommended; includes run metadata, candidate details, score dimensions, evidence and warnings.
- `promos.csv` — convenient for spreadsheet review; some nested metadata/evidence may not be represented.
- A generated raw-output ZIP containing `promos.json` — supported by the review app's ZIP upload path.

Do **not** upload the original screenplay input ZIP. Only upload generated results to a hosted instance when you are authorised to share that material with the hosting service.

### Streamlit Community Cloud

1. Push the project to GitHub without the screenplay input pack, raw outputs or `.env` file.
2. In Streamlit Community Cloud, create an app from the repository.
3. Select branch `main` and main file `app.py`.
4. Set the Python dependency file to `requirements-ui.txt` if the deployment settings ask for a dependency file. If the deployment is configured to use the root `requirements.txt`, ensure it also includes the dashboard dependencies (`streamlit` and `pandas`).
5. Deploy and test the public URL in a private/incognito browser window.

The hosted dashboard does not need `GROQ_API_KEY`; AI generation is run separately through the local CLI.

## 7. Generated outputs

A successful run writes the following files in the selected output directory:

| File | Contents |
|---|---|
| `promos.json` | Full candidate records and run metadata. This is the recommended dashboard input. |
| `promos.csv` | Flat, spreadsheet-friendly candidate list. |
| `run_report.json` | Structured run summary and per-episode status. |
| `run_report.md` | Human-readable run summary. |
| `quality_review_template.csv` | Template for recording human editorial decisions. |
| `checkpoints/` | Per-episode saved results used by `--resume`. |
| `raw_responses/` | Raw model responses saved for episodes with model output. |
| `errors/` | Per-episode error details when a model call or response parsing fails. |

Keep the output directory private unless Kuku's submission form explicitly asks you to share it. The generated evidence excerpts may reproduce short portions of the confidential screenplay.

## 8. Full-input run and quality findings

The submitted full-input run used Groq with `qwen/qwen3.8-27b` on all 50 supplied episodes.

| Measure | Observed result |
|---|---:|
| Episodes found | 50 |
| Episodes processed | 50 |
| Processing errors in final report | 0 |
| Promotional candidates retained | 98 |
| Candidates with no automated validation warnings | 24 |
| Episodes with zero candidates | 6 |

The six episodes with no retained candidates were **5, 24, 25, 28, 44 and 50**. They were processed, but the run did not retain a valid candidate for them. This does not prove that those episodes contain no usable promo moment; it means the current model-and-validation pipeline did not return one.

The validation report recorded these warning occurrences across the candidate set:

| Warning type | Occurrences |
|---|---:|
| End timestamp not close to a screenplay event/scene boundary | 43 |
| Hook evidence not within the first three seconds | 41 |
| Cliffhanger evidence not near the end | 28 |
| Start timestamp not close to a screenplay event/scene boundary | 22 |
| Hook evidence not found as an exact substring | 13 |
| Cliffhanger evidence not found as an exact substring | 13 |

Warning counts can overlap: one candidate can have more than one warning. **Zero warnings means only that the programmed checks did not flag the candidate. It is not a human approval or proof that the clip will perform well.**

One concrete failure illustrates why score and validation must be read together: the highest-ranked Episode 11 suggestion scored 100/100 but still carried four validation warnings. The score did not override those warnings.

The generated `quality_review_template.csv` is intended for a person to review the strongest candidates against the finished episode video, especially the first three seconds and the final eight seconds. A human approval rate should only be reported after that review has actually been completed; this project does not present the automated warning-free count as an editorial approval rate.

## 9. Assumptions and limitations

### Assumptions

- Screenplay timestamps are the available source of timing information and are treated as the initial timing reference.
- The first version recommends one continuous segment from one episode per promo.
- Each proposed segment must be 20–60 seconds and should use events from that episode only.
- Up to three candidates are retained per episode by default; overlapping candidates are deduplicated.
- Adjacent episode loglines may help with continuity, but timestamps from other episodes must not be used for a candidate.

### Known limitations

- **Text is not the finished video.** The system cannot verify acting, facial expression, shot composition, visual continuity, pacing, sound, music or the actual edit.
- The first version does not create multi-segment montages or combine moments across episodes.
- Model-generated hook, cliffhanger and rationale text can be inaccurate or unsupported. Evidence and warnings need to be checked against the source and video.
- Timestamp boundary checks are approximate. A screenplay event boundary is not necessarily the best editorial cut point in the finished video.
- The weighted score is a prioritisation aid, not a validated predictor of social-media performance.
- Some episodes may produce no candidates, and some candidates may still be poor despite a high score or no automated warnings.
- The model call is sequential in this implementation. Larger catalogues would need job scheduling, controlled concurrency, provider quota monitoring, retries and cost tracking.

## 10. Scaling the approach

The episode-level workflow is reusable: parse each episode, create a bounded prompt, request candidate JSON, validate the response, save a checkpoint and add candidates to a show-level ranking. For a larger catalogue, the next steps would be:

1. Run each show as a tracked job with stable input and output identifiers.
2. Cache parsed screenplay events and successful episode results so unchanged episodes are not reprocessed.
3. Add a queue and quota-aware concurrency rather than sending requests without regard to provider limits.
4. Track token usage, latency, model version, cost and per-episode failures.
5. Route the highest-ranked candidates and flagged cases to an editor, then store approval/rejection reasons as a feedback set.
6. Compare model versions against the same reviewed examples before changing the production model.

The current code supports a configurable Groq model ID and resumable episode checkpoints, but it is a prototype rather than a production-scale service. Actual cost depends on screenplay length, prompt/output tokens, model and provider pricing. It should be measured from provider usage for each show; no unmeasured per-show cost claim is made here.

## 11. Tools used

- **Python** for parsing, data models, validation, scoring, checkpointing and output generation.
- **Groq API with Qwen 3.8 27B** for candidate discovery and editorial descriptions in the full run.
- **Streamlit** for the results-review interface.
- **ChatGPT** as a development assistant for implementation discussion, debugging and documentation support.

One observed model failure: a top-ranked candidate received 100/100 while carrying four validation warnings. This reinforced the decision to surface warnings separately and keep a human editor in the loop.

## 12. Tests

Run the automated tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

The repository includes tests for core parsing, candidate and pipeline behaviour. A passing test suite checks expected code behaviour; it does not replace manual review of the generated clips against the finished videos.

## Privacy and responsible sharing

Kuku's input pack is confidential assignment material. Do not commit the original screenplay ZIP, extracted screenplay text, `.env`, API credentials or generated outputs to a public GitHub repository. Keep raw outputs in the submission location requested by Kuku. If using a hosted dashboard, upload only generated results that you are authorised to share with that hosting service. Do not expose API keys in the dashboard, repository, video or screenshots.

---

**Prototype repository:** https://github.com/sahil2448/KuKu-Assignment  
**Hosted review dashboard:** Add the final Streamlit Community Cloud URL here before sharing this README outside the repository.
