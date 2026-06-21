# Scenografia: AI Theatrical Scenic Design CLI

Scenografia is a Python 3.11+ command-line tool for generating theatrical scenic artwork from text prompts or black-and-white sketches. It is designed around reproducible output folders, configurable OpenRouter model mappings, orientation-aware generation, and validation artifacts that make each run inspectable after the fact.

## Purpose

The project focuses on theatrical scenic design rather than generic image generation. Each run is expected to preserve the generated image, the prompts that shaped it, metadata about the selected orientation and model, and a validation report for style compliance and output completeness.

## Requirements

- Python 3.11 or newer
- A local `.venv` in the repository root
- OpenRouter credentials in a local `.env` file for live generation commands
- No hardcoded secrets in source, tests, or documentation

## Setup

### Create and activate `.venv`

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -e .
```

### Configure `.env`

Create `.env` from `.env.example` and fill in only local values:

```bash
copy .env.example .env
```

Required live-generation setting:

```env
OPENROUTER_API_KEY=your-local-openrouter-key
```

Optional configuration:

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DRAFT_MODEL=your/draft-model
OPENROUTER_STANDARD_MODEL=your/standard-model
OPENROUTER_PRODUCTION_MODEL=your/production-model
OPENROUTER_VECTOR_READY_MODEL=your/vector-ready-model
APP_INPUT_DIR=input
APP_OUTPUT_DIR=output
APP_DEBUG=false
```

`OPENROUTER_API_KEY` is required only for real OpenRouter generation calls. The automated test suite does not require real credentials.

## OpenRouter Configuration

Model IDs remain configurable through `.env` so no exact Nano Banana or other provider model identifier is hardcoded in the application. The `models` command prints only per-mode model IDs or a safe configuration message. It does not print `OPENROUTER_API_KEY` or any secret value.

## Usage

Supported orientation values are:

- `portrait`
- `landscape`
- `square`

### Text prompt generation

```bash
python -m scenografia generate --prompt "fairytale medieval village with a castle in the background" --mode standard --orientation landscape
```

### Sketch generation

```bash
python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait
```

### Validate a generated image

```bash
python -m scenografia validate --image output/example/final.png
```

### Validate a completed run folder

```bash
python -m scenografia validate --run output/2026-06-21_2000_example-scene
```

### Show configured model mappings

```bash
python -m scenografia models
```

## Commands

### `generate`

Generate a scenic design from exactly one primary input:

```bash
python -m scenografia generate --prompt "..." --mode standard --orientation landscape
python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait
```

### `validate`

Validate scenic style compliance, orientation persistence, and required artifacts:

```bash
python -m scenografia validate --image output/example/final.png
python -m scenografia validate --run output/2026-06-21_2000_example-scene
```

### `models`

Show configured model IDs for:

- `draft`
- `standard`
- `production`
- `vector-ready`

Unset values are reported safely as a configuration hint rather than a fallback secret or hidden environment dump.

## Output Artifacts

Each successful generation run writes a timestamped folder under `output/`:

```text
output/
  YYYY-MM-DD_HHMM_scene-slug/
    final.png
    prompt.txt
    negative_prompt.txt
    brief.json
    generation_response.json
    validation_report.json
    processed_sketch.png
```

`processed_sketch.png` is present for sketch workflows. `generation_response.json` and `validation_report.json` record the selected orientation so the run remains traceable later.

## Testing

Run the test suite from the activated `.venv`:

```bash
.venv\Scripts\pytest tests/ --no-cov -q
```

The test suite uses mocked external services. No real OpenRouter credentials are required for tests.

## Quickstart Validation Record

The validation scenarios from [specs/001-scenic-design-cli/quickstart.md](specs/001-scenic-design-cli/quickstart.md) were checked during implementation as follows:

| Scenario | Status | Evidence |
|---|---|---|
| Text prompt generation | Verified by automated tests | `tests/test_generate_cli.py`, `tests/test_text_generation_pipeline.py` |
| Interactive orientation prompt | Verified by automated tests | `tests/test_generate_orientation_cli.py` |
| Invalid orientation rejection | Verified by automated tests | `tests/test_generate_orientation_cli.py` |
| Sketch workflow | Verified by automated tests | `tests/test_sketch_generate_cli.py`, `tests/test_sketch_interpreter_agent.py`, `tests/test_sketch_refinement.py` |
| Provider mapping behavior | Verified by automated tests | `tests/test_openrouter_client.py` |
| Configuration and model listing | Verified by automated tests | `tests/test_config.py`, `tests/test_models_cli.py` |
| Validation command and artifact completeness | Verified by automated tests | `tests/test_validate_cli.py`, `tests/test_validation_workflow.py`, `tests/test_style_contract.py` |

Live OpenRouter generation was not exercised as part of these validation runs because the automated suite is designed to pass without real credentials.
