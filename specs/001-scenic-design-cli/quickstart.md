# Quickstart: AI Scenic Design CLI Planning Validation

This document defines the validation scenarios that implementation must satisfy.

## Planned Commands

```bash
python -m scenografia generate --prompt "fairytale medieval village with a castle in the background" --mode standard --orientation landscape
python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait
python -m scenografia validate --image output/example/final.png
python -m scenografia models
```

## Validation Scenario 1: Text Prompt Generation

1. Provide a valid prompt, generation mode, and orientation.
2. Run the `generate` command.
3. Verify a timestamped output directory is created under `output/`.
4. Verify the directory contains `final.png`, `prompt.txt`, `negative_prompt.txt`,
   `brief.json`, `generation_response.json`, and `validation_report.json`.
5. Verify orientation appears in `brief.json` and `validation_report.json`.

## Validation Scenario 2: Interactive Orientation Prompt

1. Start an interactive text-mode run without `--orientation`.
2. Verify the CLI asks the user to choose `portrait`, `landscape`, or `square`.
3. Choose a valid value.
4. Verify generation continues and the selected value is persisted in artifacts.

## Validation Scenario 3: Invalid Orientation Rejection

1. Run a generate command with an unsupported orientation value.
2. Verify the CLI rejects the value with user-visible failure feedback.
3. Verify no partial output directory is left behind as a successful run.

## Validation Scenario 4: Sketch Workflow

1. Provide a valid black-and-white sketch, mode, style, and orientation.
2. Run the sketch-based `generate` command.
3. Verify local preprocessing occurs before any optional AI refinement path.
4. Verify `processed_sketch.png` exists in the output directory.
5. Verify orientation is included in prompt and validation artifacts.

## Validation Scenario 5: Provider Mapping Behavior

1. Run a generation using a model configuration that supports explicit aspect ratio.
2. Verify the provider adapter includes orientation-derived image configuration.
3. Run a generation using a configuration that does not support explicit aspect ratio.
4. Verify orientation still appears in the final prompt.

## Validation Scenario 6: Configuration and Model Listing

1. Run the planned `models` command.
2. Verify configured generation modes and their model mappings are presented without exposing secrets.
3. Verify missing required configuration produces clear user-facing errors.