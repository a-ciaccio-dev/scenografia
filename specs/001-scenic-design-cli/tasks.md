---

description: "Task list for implementing the AI Scenic Design CLI"

---

# Tasks: AI Scenic Design CLI

**Input**: Design documents from `/specs/001-scenic-design-cli/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are included because the approved plan explicitly requires configuration, orientation, prompt, provider, preprocessing, output manager, and CLI validation coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, local environment setup, and repository scaffolding

- [X] T001 Create project metadata, dependency declarations, and CLI entrypoint configuration in pyproject.toml
- [X] T002 Create local environment template for OpenRouter and app directories in .env.example
- [X] T003 Create repository ignore rules for `.venv`, `.env`, Python caches, and temporary files in .gitignore
- [X] T004 Document local `.venv` bootstrap and planned CLI commands in README.md
- [X] T005 Create package entrypoint scaffolding in src/scenografia/__init__.py and src/scenografia/main.py
- [X] T006 [P] Create agent package scaffolding in src/scenografia/agents/__init__.py
- [X] T007 [P] Create tool package scaffolding in src/scenografia/tools/__init__.py
- [X] T008 [P] Create schema package scaffolding in src/scenografia/schemas/__init__.py
- [X] T009 [P] Create test fixture scaffolding for sketch preprocessing in tests/fixtures/sketch_dummy.png
- [X] T010 Create the local virtual environment in .venv/ and install project dependencies from pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration, schemas, tools, and tests that block all user stories

**✅ COMPLETE**: Phase 2 foundational tests all passing (108/108 tests)

- [X] T011 [P] Add configuration loading and mode-to-model mapping tests in tests/test_config.py
- [X] T012 [P] Add orientation enum, validation, and non-interactive failure tests in tests/test_orientation.py
- [X] T013 [P] Add scenic style contract and prompt template tests in tests/test_prompt_templates.py
- [X] T014 [P] Add output artifact persistence tests in tests/test_output_manager.py
- [X] T015 [P] Add mocked OpenRouter client and provider adapter tests in tests/test_openrouter_client.py
- [X] T016 [P] Add local sketch preprocessing tests with the dummy fixture in tests/test_sketch_preprocessor.py
- [X] T017 Implement environment configuration loading and configurable mode-to-model mapping in src/scenografia/config.py
- [X] T018 [P] Implement Orientation enum and GenerationRequest schema in src/scenografia/schemas/generation_schema.py
- [X] T019 [P] Implement StructuredBrief schema in src/scenografia/schemas/brief_schema.py
- [X] T020 [P] Implement SketchInterpretation schema in src/scenografia/schemas/sketch_schema.py
- [X] T021 [P] Implement GenerationMetadata and ValidationReport schemas in src/scenografia/schemas/validation_schema.py
- [X] T022 [P] Implement scenic prompt template primitives and negative constraint helpers in src/scenografia/tools/prompt_templates.py
- [X] T023 [P] Implement OpenRouter client and provider adapter orientation mapping in src/scenografia/tools/openrouter_client.py
- [X] T024 [P] Implement timestamped output directory creation and artifact persistence in src/scenografia/tools/output_manager.py
- [X] T025 [P] Implement local black-and-white sketch preprocessing in src/scenografia/tools/image_preprocessor.py
- [X] T026 [P] Implement scenic style validation helpers in src/scenografia/tools/style_validator.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Generate Scenic Design From Text Prompt (Priority: P1) 🎯 MVP

**Goal**: Generate a scenic image from a text prompt with validated orientation, prompt construction, provider request mapping, and persisted artifacts

**Independent Test**: Run `python -m scenografia generate --prompt "..." --mode standard --orientation landscape` and verify the scenic image plus required artifacts are created under a timestamped output folder

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST and ensure they fail before implementation**

- [X] T027 [P] [US1] Add text-mode generate happy-path CLI tests in tests/test_generate_cli.py
- [X] T028 [P] [US1] Add `--orientation`, interactive fallback, and invalid orientation tests in tests/test_generate_orientation_cli.py
- [X] T029 [P] [US1] Add mocked text-generation pipeline tests covering prompt, metadata, and validation artifacts in tests/test_text_generation_pipeline.py

### Implementation for User Story 1

- [X] T030 [P] [US1] Implement text normalization and StructuredBrief creation in src/scenografia/agents/brief_agent.py
- [X] T031 [P] [US1] Implement orientation-aware final prompt and negative prompt generation in src/scenografia/agents/prompt_engineer_agent.py
- [X] T032 [P] [US1] Implement text-mode generation orchestration and provider adapter usage in src/scenografia/agents/image_generation_agent.py
- [X] T033 [US1] Implement the `generate` text-mode CLI flow with `--orientation` and interactive fallback in src/scenografia/main.py
- [X] T034 [US1] Integrate text-mode prompt, metadata, and validation artifact persistence in src/scenografia/main.py

**Checkpoint**: User Story 1 should be fully functional and independently testable

---

## Phase 4: User Story 2 - Generate Scenic Design From Black-and-White Sketch (Priority: P2)

**Goal**: Generate a scenic image from a black-and-white sketch using local preprocessing, optional AI refinement, and the same orientation-aware output guarantees as text mode

**Independent Test**: Run `python -m scenografia generate --sketch input/sketches/sketch.png --style "fairytale theatrical backdrop" --mode vector-ready --orientation portrait` and verify `processed_sketch.png`, the final image, and all required artifacts are persisted

### Tests for User Story 2 ⚠️

- [X] T035 [P] [US2] Add sketch interpreter agent tests with local preprocessing fixtures in tests/test_sketch_interpreter_agent.py
- [X] T036 [P] [US2] Add sketch-mode CLI tests covering processed sketch output and style guidance in tests/test_sketch_generate_cli.py
- [X] T037 [P] [US2] Add optional AI refinement toggle tests for sketch mode in tests/test_sketch_refinement.py

### Implementation for User Story 2

- [X] T038 [P] [US2] Implement local sketch preprocessing and optional AI refinement orchestration in src/scenografia/agents/sketch_interpreter_agent.py
- [X] T039 [US2] Extend sketch interpretation to StructuredBrief transformation in src/scenografia/agents/brief_agent.py
- [X] T040 [US2] Extend image generation orchestration for sketch-based requests in src/scenografia/agents/image_generation_agent.py
- [X] T041 [US2] Extend the `generate` CLI flow for `--sketch`, `--style`, and `processed_sketch.png` persistence in src/scenografia/main.py

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Validate Style Compliance And Output Traceability (Priority: P3)

**Goal**: Validate scenic style compliance, orientation persistence, and artifact completeness for generated runs

**Independent Test**: Run `python -m scenografia validate --image output/example/final.png` or validate a completed run folder and verify the resulting report captures style, orientation, and artifact completeness

### Tests for User Story 3 ⚠️

- [X] T042 [P] [US3] Add style compliance and validation report tests in tests/test_style_contract.py
- [X] T043 [P] [US3] Add `validate` command and artifact completeness tests in tests/test_validate_cli.py
- [X] T044 [P] [US3] Add orientation persistence tests for metadata and validation reports in tests/test_validation_workflow.py

### Implementation for User Story 3

- [X] T045 [P] [US3] Implement scenic style, orientation, and artifact completeness checks in src/scenografia/agents/style_compliance_agent.py
- [X] T046 [US3] Extend validation report and orientation metadata persistence in src/scenografia/tools/output_manager.py
- [X] T047 [US3] Implement the `validate` CLI command for generated images and run folders in src/scenografia/main.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish auxiliary CLI behavior, documentation, and end-to-end validation

- [X] T048 [P] Add configurable model listing tests for generation modes in tests/test_models_cli.py
- [X] T049 Implement the `models` CLI command without exposing secrets in src/scenografia/main.py
- [X] T050 [P] Refresh project usage, `.venv` workflow, and generation examples in README.md
- [X] T051 [P] Refine environment variable comments and configurable model placeholders in .env.example
- [X] T052 Run the validation scenarios from specs/001-scenic-design-cli/quickstart.md and record the results in README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP slice
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses User Story 1 generation flow
- **User Story 3 (Phase 5)**: Depends on Foundational completion and validates generated runs from US1/US2
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependency on other stories
- **User Story 2 (P2)**: Can start after Foundational - reuses shared generation infrastructure but remains independently testable
- **User Story 3 (P3)**: Can start after Foundational - validates outputs from completed generation flows

### Within Each User Story

- Tests MUST be written and fail before implementation
- Shared schemas and tools come before agents
- Agents come before CLI orchestration
- CLI orchestration comes before end-to-end artifact validation

### Parallel Opportunities

- Setup tasks marked `[P]` can run in parallel after the base package entrypoint exists
- Foundational test tasks and schema/tool tasks marked `[P]` can run in parallel by file
- User story tests marked `[P]` can run in parallel by file
- Different user stories can be developed in parallel after Foundational completion if interfaces remain stable

---

## Parallel Example: Foundational Phase

```bash
# Launch shared validation tests together:
Task: "Add configuration loading and mode-to-model mapping tests in tests/test_config.py"
Task: "Add orientation enum, validation, and non-interactive failure tests in tests/test_orientation.py"
Task: "Add output artifact persistence tests in tests/test_output_manager.py"

# Launch shared implementation tasks together:
Task: "Implement Orientation enum and GenerationRequest schema in src/scenografia/schemas/generation_schema.py"
Task: "Implement StructuredBrief schema in src/scenografia/schemas/brief_schema.py"
Task: "Implement GenerationMetadata and ValidationReport schemas in src/scenografia/schemas/validation_schema.py"
```

---

## Parallel Example: User Story 1

```bash
# Launch text-mode tests together:
Task: "Add text-mode generate happy-path CLI tests in tests/test_generate_cli.py"
Task: "Add --orientation, interactive fallback, and invalid orientation tests in tests/test_generate_orientation_cli.py"

# Launch text-mode implementation tasks together:
Task: "Implement text normalization and StructuredBrief creation in src/scenografia/agents/brief_agent.py"
Task: "Implement orientation-aware final prompt and negative prompt generation in src/scenografia/agents/prompt_engineer_agent.py"
Task: "Implement text-mode generation orchestration and provider adapter usage in src/scenografia/agents/image_generation_agent.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate text-mode generation, orientation behavior, and artifact output

### Incremental Delivery

1. Deliver text-mode generation with orientation handling
2. Add sketch-mode generation with local preprocessing and optional AI refinement
3. Add validation and traceability command coverage
4. Finish with model listing and quickstart validation

### Team Strategy

1. One developer completes setup and shared foundations
2. One developer focuses on US1 while another prepares US2 test files
3. US3 validation work begins after the generation artifact contracts stabilize

---

## Notes

- Orientation handling is covered end-to-end: enum values, CLI option, interactive fallback, invalid input failure, propagation into GenerationRequest, StructuredBrief, prompt composition, metadata, validation report, and provider adapter mapping
- Model IDs remain configurable through `.env` and/or CLI overrides; tasks do not assume the exact Nano Banana model ID
- The task list preserves a CLI-only MVP with no database and no web UI