# Implementation Plan: AI Scenic Design CLI

**Branch**: `001-scenic-design-cli` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-scenic-design-cli/spec.md`

## Summary

Build a Python 3.11+ CLI application that generates theatrical scenic designs from
either a text prompt or a black-and-white sketch using OpenRouter and a
configurable image model. The MVP remains CLI-only, file-based, and database-free.
The architecture uses a small pipeline of agents and reusable tools that capture a
mandatory orientation value before generation, transform input into a structured
brief and prompt package, optionally refine sketch interpretation, call OpenRouter,
validate scenic style compliance, and persist reproducible artifacts under
timestamped `output/` directories.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `httpx`, `python-dotenv`, `pydantic`, `Pillow`,
`opencv-python`, `numpy`, `typer`, `pytest`, optional `rich`

**Storage**: Local filesystem only (`input/`, `output/`, `.env`, JSON and text artifacts)

**Testing**: `pytest` with temporary directories, mocked OpenRouter responses, and
dummy sketch fixtures

**Target Platform**: Local command-line environments on Windows, macOS, and Linux

**Project Type**: Single-project Python CLI application

**Performance Goals**: Complete a single generation workflow within one CLI session,
persist all required artifacts atomically, and keep prompt preparation and sketch
preprocessing lightweight relative to remote image generation time

**Constraints**: `.venv` only, no global dependency installation, no database,
no web UI, no hardcoded model IDs or API keys, no application dependency
installation during planning, orientation is mandatory before generation

**Scale/Scope**: Single-user local CLI MVP, one generation request at a time,
text and sketch input modes, four generation modes (`draft`, `standard`,
`production`, `vector-ready`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Python-first and CLI-first architecture preserved.
- [x] `.venv` is the only application dependency environment and `pyproject.toml`
  is the source of dependency intent.
- [x] Secrets are sourced from `.env` or equivalent local environment injection;
  no keys are hardcoded or committed.
- [x] Output design persists the final image, final prompt, negative prompt,
  structured brief, generation metadata, validation report, and processed
  sketch when applicable.
- [x] All generated artifacts are written under `output/` with timestamped,
  human-readable run directories.
- [x] The scenic style contract is enforced in prompt generation and validation.
- [x] The architecture names distinct agents or tools with single responsibilities
  and clear test seams.
- [x] Tasks, implementation, commit, and push remain blocked until explicit user
  approval after planning.

## Project Structure

### Documentation (this feature)

```text
specs/001-scenic-design-cli/
├── plan.md              # This file
├── research.md          # Phase 0 decisions and rationale
├── data-model.md        # Phase 1 domain models and validation rules
├── quickstart.md        # Phase 1 validation scenarios
├── contracts/           # Phase 1 CLI and provider contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scenografia/
├── input/
│   └── sketches/
├── output/
src/
│   └── scenografia/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── brief_agent.py
│       │   ├── sketch_interpreter_agent.py
│       │   ├── prompt_engineer_agent.py
│       │   ├── image_generation_agent.py
│       │   └── style_compliance_agent.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── openrouter_client.py
│       │   ├── image_preprocessor.py
│       │   ├── output_manager.py
│       │   ├── prompt_templates.py
│       │   └── style_validator.py
│       └── schemas/
│           ├── __init__.py
│           ├── brief_schema.py
│           ├── sketch_schema.py
│           ├── generation_schema.py
│           └── validation_schema.py

tests/
├── test_prompt_templates.py
├── test_output_manager.py
├── test_config.py
├── test_orientation.py
├── test_openrouter_client.py
├── test_style_contract.py
└── fixtures/
    └── sketch_dummy.png

.env.example
.gitignore
pyproject.toml
README.md
```

**Structure Decision**: Use a single Python CLI project rooted at the repository
root. Keep agents under `src/scenografia/agents/`, reusable tools under
`src/scenografia/tools/`, typed schemas under `src/scenografia/schemas/`, and keep
tests flat and feature-focused for the MVP. No additional projects, services, web
applications, or databases are introduced.

## Complexity Tracking

No constitution violations require justification in this plan.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Outcomes

- Keep orchestration manual and explicit; do not introduce heavyweight AI agent
  frameworks for the MVP.
- Use `typer` for commands and interactive prompting because orientation is a
  mandatory pre-generation input and interactive fallback is a core UX requirement.
- Represent orientation as a shared enum in schemas and route it through CLI,
  request models, prompt composition, provider mapping, metadata, and validation.
- Use a provider adapter layer to translate orientation into OpenRouter
  request-specific image configuration when supported, while always encoding
  orientation in the final prompt as a fallback.
- Treat exact OpenRouter aspect ratio field names and the exact Nano Banana model
  ID as planned open decisions to confirm during implementation.

## Phase 1: Design Decisions

### Architecture Overview

The runtime flow for `generate` is:

1. CLI command parses input mode, generation mode, optional model override, and
   mandatory orientation.
2. If orientation is missing in an interactive run, the CLI prompts the user to
   choose `portrait`, `landscape`, or `square`.
3. `BriefAgent` normalizes input into a `GenerationRequest` and `StructuredBrief`.
4. `SketchInterpreterAgent` runs only for sketch mode and calls local
   preprocessing first, then optional AI vision refinement if enabled.
5. `PromptEngineerAgent` creates the final prompt and negative prompt, enforcing
   scenic style constraints and orientation-aware composition.
6. `ImageGenerationAgent` uses `OpenRouterClient` plus a provider adapter to send
   the configured image request.
7. `StyleComplianceAgent` validates scenic style contract application, artifact
   completeness, and orientation capture.
8. `OutputManager` writes all artifacts under a timestamped run directory.

### CLI Surface

- `python -m scenografia generate --prompt "description" --mode standard --orientation landscape`
- `python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait`
- `python -m scenografia validate --image output/example/final.png`
- `python -m scenografia models`

### Dependency Rationale

- `httpx`: HTTP client for OpenRouter, request retries, timeouts, and mocked tests.
- `python-dotenv`: local environment loading for `.env` without embedding secrets.
- `pydantic`: typed schemas for request, brief, metadata, validation, and adapter data.
- `Pillow`: file I/O for generated images and processed sketches.
- `opencv-python`: local black-and-white sketch preprocessing.
- `numpy`: image-processing array operations used by preprocessing.
- `typer`: CLI commands, choice validation, and interactive prompt behavior.
- `pytest`: configuration, orientation, prompt, client, preprocessing, and output tests.
- `rich` optional: improved readability for future CLI reporting, not MVP-blocking.

### Orientation Representation

- Define an `Orientation` enum or equivalent schema with exactly three values:
  `portrait`, `landscape`, `square`.
- Include `orientation` in `GenerationRequest` and `StructuredBrief`.
- Include `orientation` in generation metadata and validation report.
- Add a provider adapter mapping `orientation -> provider image configuration`
  for models that expose aspect ratio or size settings.
- Always include the orientation intent in the final prompt even when explicit
  provider orientation fields are unavailable.

### Configuration Plan

Planned configuration variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `OPENROUTER_DEFAULT_MODEL`
- `APP_INPUT_DIR=input`
- `APP_OUTPUT_DIR=output`

Generation modes:

- `draft`
- `standard`
- `production`
- `vector-ready`

Each mode maps to a configurable OpenRouter model ID through configuration, not
through hardcoded source constants.

### File Creation Intent

Implementation is expected to create and maintain the following project files, but
they are not created during this planning phase:

- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `README.md`

### Post-Design Constitution Check

- [x] Python-first and CLI-only architecture preserved after detailed design.
- [x] `.venv`, `.env`, `.env.example`, and `pyproject.toml` are first-class planned artifacts.
- [x] Output reproducibility includes final image, prompts, brief, metadata,
  validation report, and processed sketch when applicable.
- [x] Scenic style and negative constraints are enforced in prompt generation and validation.
- [x] Orientation is represented across CLI input, schemas, provider mapping,
  metadata, and validation as required by the updated specification.
- [x] Tasks, implementation, commit, and push remain blocked pending user approval.
