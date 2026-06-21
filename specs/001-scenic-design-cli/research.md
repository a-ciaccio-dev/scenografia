# Research: AI Scenic Design CLI

## Decision: Use a manual Python agent pipeline instead of an orchestration framework

**Rationale**: The Constitution requires a Python-first, modular, testable CLI with
clear agent responsibilities. A manual pipeline of small modules preserves explicit
data flow and keeps testing simple.

**Alternatives considered**:
- LangChain-like orchestration frameworks: rejected as unnecessary complexity for an MVP.
- Single monolithic generator service: rejected because it hides responsibilities and weakens test seams.

## Decision: Use `typer` for the CLI surface

**Rationale**: The CLI must support explicit `--orientation`, interactive fallback
for missing orientation, and multiple subcommands. `typer` provides clear command
definitions, type-aware validation, and interactive prompting without custom parser
boilerplate.

**Alternatives considered**:
- `argparse`: workable but less ergonomic for typed commands and interactive prompts.
- Click directly: rejected because `typer` provides a cleaner Python typing model.

## Decision: Model runtime contracts with `pydantic`

**Rationale**: The application requires strongly defined schemas for Generation
Request, Structured Brief, orientation, metadata, and validation output. `pydantic`
supports validation, serialization, and consistent JSON artifacts.

**Alternatives considered**:
- Dataclasses plus manual validation: rejected because validation logic would scatter.
- Plain dictionaries: rejected due to weak contract enforcement and harder testing.

## Decision: Use `httpx` with a provider adapter for OpenRouter integration

**Rationale**: `httpx` is modern, testable, and supports straightforward request
mocking. A provider adapter isolates model-specific request fields such as aspect
ratio or size, which is necessary because orientation must influence provider
configuration when supported.

**Alternatives considered**:
- `requests`: rejected because `httpx` offers a better forward path for async if needed later.
- Hardcoded request shapes in the agent: rejected because provider-specific logic would spread across modules.

## Decision: Use local image preprocessing as the non-optional base for sketch mode

**Rationale**: The specification fixes a Hybrid strategy, so local preprocessing is
always required before optional AI vision refinement. `opencv-python`, `numpy`, and
`Pillow` provide the needed local operations while preserving reproducible inputs.

**Alternatives considered**:
- AI-only sketch interpretation: rejected because it violates the Hybrid constraint.
- Pillow-only preprocessing: rejected because contour and threshold workflows are better served by OpenCV.

## Decision: Keep MVP storage file-based with no database

**Rationale**: The Constitution prioritizes simplicity and reproducible artifacts.
The spec requires local `output/` folders, and no multi-user or querying use case
requires a database in the MVP.

**Alternatives considered**:
- SQLite metadata storage: rejected as premature for a CLI-first MVP.
- Remote artifact storage: rejected because it adds infrastructure without spec value.

## Decision: Orientation must be represented in every stage of the workflow

**Rationale**: Orientation is now a mandatory pre-generation input. It must exist as
validated user input, schema data, prompt guidance, provider mapping input, saved
metadata, and validation output.

**Alternatives considered**:
- Prompt-only orientation: rejected because it fails provider configuration and auditability requirements.
- Provider-only orientation: rejected because some models may not expose an orientation field.

## Decision: Defer exact OpenRouter orientation request field and exact Nano Banana model ID

**Rationale**: The plan must preserve configurable model IDs and avoid hardcoding
unverified provider details. A provider adapter allows implementation to confirm the
exact field names later without reshaping the architecture.

**Alternatives considered**:
- Hardcode a guessed aspect-ratio field now: rejected because it risks invalid API coupling.
- Hardcode a guessed Nano Banana model ID: rejected because the specification requires configurability.