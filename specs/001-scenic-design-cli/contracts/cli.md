# CLI Contract: AI Scenic Design CLI

## Command: `generate`

### Purpose

Generate a theatrical scenic design from either text or sketch input.

### Inputs

- `--prompt <text>`: text prompt input mode
- `--sketch <path>`: sketch input mode
- `--style <text>`: optional style guidance for sketch mode
- `--mode <draft|standard|production|vector-ready>`: required generation mode
- `--orientation <portrait|landscape|square>`: optional in interactive runs, required in non-interactive runs
- `--model <model-id>`: optional per-run override
- `--disable-ai-refinement`: optional sketch-mode flag

### Behavioral Rules

- Exactly one of `--prompt` or `--sketch` selects the primary input mode.
- If `--orientation` is absent in an interactive run, the CLI must prompt the user.
- If `--orientation` is absent in a non-interactive run, the command must fail visibly.
- Invalid orientation values must fail visibly.
- Successful runs must persist the required artifact set under `output/`.

## Command: `validate`

### Purpose

Validate a generated image or run folder against scenic style and artifact expectations.

### Inputs

- `--image <path>`: validate from a generated image path

### Outputs

- Human-readable validation result
- Optional structured report generation in future iterations

## Command: `models`

### Purpose

List configured generation modes and their associated OpenRouter model mappings.

### Outputs

- Available generation modes
- Configured default model mapping per mode
- No secrets displayed