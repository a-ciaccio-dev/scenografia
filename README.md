# Scenografia: AI Theatrical Scenic Design CLI

Scenografia is a Python 3.11+ command-line tool for generating theatrical scenic artwork from text prompts or black-and-white sketches. It is designed around reproducible output folders, configurable image generation model mappings, orientation-aware generation, and validation artifacts that make each run inspectable after the fact.

## Purpose

The project focuses on theatrical scenic design rather than generic image generation. Each run is expected to preserve the generated image, the prompts that shaped it, metadata about the selected orientation and model, and a validation report for style compliance and output completeness.

## Requirements

- Python 3.11 or newer
- A local `.venv` in the repository root
- **OpenRouter API credentials** in a local `.env` file for live generation commands
  - Get a free account at [openrouter.ai](https://openrouter.ai)
  - Generate an API key from your account settings
  - Note: You must have a model with `output_modalities=image` enabled for your account
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
OPENROUTER_API_KEY=your-openrouter-api-key
```

Optional configuration:

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DRAFT_MODEL=google/gemini-2.5-flash-image
OPENROUTER_STANDARD_MODEL=google/gemini-2.5-flash-image
OPENROUTER_PRODUCTION_MODEL=google/gemini-2.5-flash-image
OPENROUTER_VECTOR_READY_MODEL=google/gemini-2.5-flash-image
APP_INPUT_DIR=input
APP_OUTPUT_DIR=output
APP_DEBUG=false
```

`OPENROUTER_API_KEY` (your OpenRouter API key) is required only for real image generation calls. The automated test suite does not require real credentials.

### Model Configuration

Model IDs must be OpenRouter model identifiers with `output_modalities=image` support.

**Recommended starter model**:
- **Google Gemini 2.5 Flash Image**: `google/gemini-2.5-flash-image` (good balance of quality and speed)

**Other options** (verify image output support on your OpenRouter account):
- Any OpenRouter model with `output_modalities=image` enabled
- You can find available models at [openrouter.ai/models](https://openrouter.ai/models)

**Important**: The model must explicitly support image output. If a model does not support `output_modalities=image`, generation will fail.

## Usage

Supported orientation values are:

- `portrait`
- `landscape`
- `square`

### Text prompt generation

```bash
# Via python -m scenografia
python -m scenografia generate --prompt "fairytale medieval village with a castle in the background" --mode standard --orientation landscape

# Or via python -m scenografia.main
python -m scenografia.main generate --prompt "fairytale medieval village with a castle in the background" --mode standard --orientation landscape
```

### Sketch generation

```bash
# Via python -m scenografia
python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait

# Or via python -m scenografia.main
python -m scenografia.main generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait
```

### Validate a generated image

```bash
python -m scenografia.main validate --image output/example/final.png
```

### Validate a completed run folder

```bash
python -m scenografia.main validate --run output/2026-06-21_2000_example-scene
```
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
