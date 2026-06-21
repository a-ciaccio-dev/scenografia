# Feature Specification: AI Scenic Design CLI

**Feature Branch**: `001-scenic-design-cli`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Create the Specification in English for a Python CLI application that generates theatrical scenic designs using AI agents and OpenRouter."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Scenic Design From Text Prompt (Priority: P1)

A CLI user provides a textual description of the desired theatrical scenic design, selects the desired output orientation, and receives a generated scenic image plus all required traceability artifacts in a single run.

**Why this priority**: Text-driven generation is the smallest valuable slice of the product because it proves the end-to-end scenic generation workflow without depending on sketch analysis.

**Independent Test**: Can be fully tested by running the CLI with a valid text prompt and a valid orientation, then verifying that a scenic image and the required artifact set are saved under a timestamped output folder.

**Acceptance Scenarios**:

1. **Given** the user provides a valid text prompt and a configured image model, **When** the user runs the generate command with a supported orientation or chooses one interactively, **Then** the system produces a scenic image and saves all required output artifacts under a timestamped `output/` subfolder.
2. **Given** the user provides a valid text prompt, **When** the system prepares the generation request, **Then** it captures a valid orientation selection, creates a structured brief, a final prompt, a negative prompt, and applies the scenic style contract before image generation.
3. **Given** the image generation request completes, **When** the run is finalized, **Then** the user can inspect the saved prompt, negative prompt, brief, generation response, and validation report alongside the final image.
4. **Given** the user does not provide `--orientation` in an interactive CLI run, **When** the system has enough information to continue, **Then** it asks the user to choose one of `portrait`, `landscape`, or `square` before image generation proceeds.

---

### User Story 2 - Generate Scenic Design From Black-and-White Sketch (Priority: P2)

A CLI user provides a black-and-white sketch, optional style guidance, and a desired output orientation so the system can interpret the sketch, turn it into a scenic description, and produce a theatrical scenic image with the same artifact guarantees as text mode.

**Why this priority**: Sketch-driven generation is a core differentiator, but it depends on the same output and image generation flow already established by the text-based workflow.

**Independent Test**: Can be fully tested by running the CLI with a valid black-and-white sketch, a valid orientation, and optional style input, then verifying the presence of the final image, structured interpretation artifacts, and processed sketch output.

**Acceptance Scenarios**:

1. **Given** the user provides a valid black-and-white sketch file and a supported orientation, **When** the user runs the generate command in sketch mode, **Then** the system preprocesses the sketch locally, derives a scenic interpretation, and saves the processed sketch with the final output artifacts.
2. **Given** AI vision refinement is enabled for a run, **When** the system interprets the sketch, **Then** local preprocessing remains the base step and the optional AI refinement augments rather than replaces the sketch interpretation flow.
3. **Given** the sketch interpretation is completed, **When** the system prepares image generation, **Then** it produces a structured scenic description and a final prompt that comply with the scenic style contract, negative constraints, and selected orientation.

---

### User Story 3 - Validate Style Compliance And Output Traceability (Priority: P3)

A CLI user wants confidence that generated scenic artwork follows the required scenic style contract, respects the chosen orientation, and can be reviewed later through saved validation and metadata artifacts.

**Why this priority**: Style compliance and reproducibility are mandatory quality guarantees, but they add value only after generation workflows exist.

**Independent Test**: Can be fully tested by inspecting the artifacts of a completed run and confirming that the validation report records whether style, orientation handling, and negative constraints were enforced and that all mandatory files are present.

**Acceptance Scenarios**:

1. **Given** a generation run completes in either input mode, **When** validation is finalized, **Then** the system creates a validation report that records scenic style compliance, the selected orientation, and any unmet constraints.
2. **Given** a generation run completes successfully, **When** the output folder is inspected, **Then** it contains the required files for that mode using the required timestamped and human-readable folder structure.

### Edge Cases

- What happens when the user runs the CLI without providing either a text prompt or a sketch input?
- What happens when both a text prompt and a sketch are provided in a way that creates ambiguous intent for a single generation command?
- What happens when the user provides an unsupported orientation value?
- What happens when `--orientation` is omitted in a non-interactive CLI context where the system cannot ask the user to choose one?
- How does the system handle a sketch file that is unreadable, missing, or not actually black-and-white compatible with the sketch workflow?
- How does the system handle an OpenRouter request failure after the brief and prompts have already been prepared?
- How does the system behave when optional AI vision refinement is disabled or unavailable for a sketch run?
- How does the system handle output folder name collisions for multiple runs created within the same minute?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a CLI-only first release for generating theatrical scenic designs.
- **FR-002**: The system MUST accept a text prompt input mode in which the user supplies a textual scenic description.
- **FR-003**: The system MUST accept a black-and-white sketch input mode in which the user supplies a sketch image and may optionally provide style guidance.
- **FR-004**: The system MUST normalize the user request before image generation so downstream steps operate on a consistent scenic intent.
- **FR-005**: The system MUST collect the desired output orientation for every generation run before requesting image generation.
- **FR-006**: The system MUST support `portrait`, `landscape`, and `square` as the only allowed orientation values.
- **FR-007**: The system MUST support an explicit `--orientation` CLI option.
- **FR-008**: If `--orientation` is not provided in an interactive CLI run, the system MUST ask the user to choose one of the allowed orientation values before image generation proceeds.
- **FR-009**: The system MUST validate that the selected orientation is one of the allowed values and MUST provide user-visible failure feedback for unsupported or invalid values.
- **FR-010**: The system MUST include the selected orientation in the Generation Request.
- **FR-011**: The system MUST include the selected orientation in the Structured Brief.
- **FR-012**: The system MUST create a structured brief for every generation run before requesting image generation.
- **FR-013**: The system MUST create a final prompt and a negative prompt for every generation run.
- **FR-014**: The system MUST ensure the selected orientation influences the final prompt sent to the image model.
- **FR-015**: The system MUST apply the scenic style contract to every generation request, including full color, solid fills, hand-drawn or hand-painted theatrical scenic look, clean outlines, closed paths where visually possible, and layer separation awareness for future SVG export.
- **FR-016**: The system MUST enforce the negative constraints for every generation request, including no photorealism, no 3D render look, no blurry edges, no text, no logos, no watermark, no excessive micro-details, and a preference for large readable shapes, clear silhouettes, separated foreground/midground/background, and simplified color regions.
- **FR-017**: In sketch mode, the system MUST preprocess the sketch locally as the base interpretation step.
- **FR-018**: In sketch mode, the system MUST support optional and configurable AI vision refinement through OpenRouter without removing the local preprocessing base step.
- **FR-019**: In sketch mode, the system MUST transform the interpreted sketch into a structured scenic description before final prompt generation.
- **FR-020**: The system MUST call OpenRouter to request image generation using a configured image model.
- **FR-021**: The system MUST pass the selected orientation to the OpenRouter image generation request when the selected model supports aspect ratio or image configuration.
- **FR-022**: The system MUST NOT hardcode the OpenRouter model ID and MUST allow the image model selection to be configured through `.env`, CLI input, or both.
- **FR-023**: The system MUST load the OpenRouter API key from local environment configuration rather than embedding it in code or saved prompts.
- **FR-024**: The system MUST save generation artifacts under `output/` in a timestamped, human-readable subfolder for each run.
- **FR-025**: The system MUST save the final image as `final.png` for successful generation runs.
- **FR-026**: The system MUST save the final prompt as `prompt.txt` and the negative prompt as `negative_prompt.txt` for every run.
- **FR-027**: The system MUST save the structured brief as `brief.json` for every run.
- **FR-028**: The system MUST save the generation response metadata as `generation_response.json` for every run that reaches the image generation stage.
- **FR-029**: The system MUST save a validation result as `validation_report.json` for every run.
- **FR-030**: The system MUST save `processed_sketch.png` when the input mode uses a sketch.
- **FR-031**: The system MUST structure output folders using the pattern `YYYY-MM-DD_HHMM_scene-slug` or an equivalent human-readable timestamp-first naming convention.
- **FR-032**: The system MUST expose a Brief Agent, Sketch Interpreter Agent, Prompt Engineer Agent, Image Generation Agent, Style Compliance Agent, and Output Manager Tool as distinct responsibilities within the generation workflow.
- **FR-033**: The system MUST allow the sketch interpretation strategy to remain Hybrid, where local preprocessing is always required and AI vision refinement is optional and configurable.
- **FR-034**: The system MUST save the selected orientation in generation metadata.
- **FR-035**: The system MUST save the selected orientation in the validation report.
- **FR-036**: The system MUST produce a validation report that records whether the scenic style contract and negative constraints were applied to the run.
- **FR-037**: The system MUST provide user-visible failure feedback when a generation run cannot proceed because required input, required configuration, sketch loading, external generation, or orientation validation fails.
- **FR-038**: The system MUST preserve the first-release scope as CLI-only and MUST NOT require a graphical interface for generation.

### Key Entities *(include if feature involves data)*

- **Generation Request**: A user-initiated generation run that captures the input mode, user intent, selected orientation, optional style guidance, configured model selection, and requested generation mode.
- **Structured Brief**: A normalized scenic description derived from text or sketch input that defines the intended scene composition, selected orientation, style goals, and generation constraints.
- **Prompt Package**: The pair of final prompt and negative prompt prepared for image generation, including orientation-aware prompt guidance.
- **Sketch Interpretation**: The structured result of local preprocessing and optional AI refinement for a black-and-white sketch input.
- **Generation Artifact Set**: The collection of persisted files for a run, including the final image, prompt files, structured brief, validation report, generation response metadata, and processed sketch when applicable, plus recorded orientation metadata.
- **Validation Report**: The recorded outcome of style compliance, orientation capture, and artifact completeness checks for a generation run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a successful text-to-scenic generation run and locate all required output artifacts within one CLI session without manual file reconstruction.
- **SC-002**: Users can complete a successful sketch-to-scenic generation run and retrieve both the processed sketch artifact and the final scenic image from the same output folder.
- **SC-003**: 100% of successful generation runs produce the mandatory artifact set required for their selected input mode.
- **SC-004**: 100% of generation runs capture a valid orientation value before image generation begins.
- **SC-005**: 100% of successful generation runs record the selected orientation in generation metadata and the validation report.
- **SC-006**: 100% of generation runs record whether scenic style and negative constraints were applied in the validation report.
- **SC-007**: Users can identify the correct run folder for a completed generation from its timestamped, human-readable name without opening multiple directories.
- **SC-008**: Users can switch the OpenRouter image model for a run through configuration without modifying source code.

## Assumptions

- Users run the first release from a local CLI environment and have access to OpenRouter credentials through local environment configuration.
- The first release targets one generation request at a time rather than bulk or batch generation.
- Interactive CLI sessions can prompt the user for missing orientation input, while non-interactive runs must provide orientation explicitly.
- The output folder is writable by the user running the CLI.
- Optional AI vision refinement may be disabled for some runs without preventing the base sketch workflow from completing.
- Specification and planning artifacts for this project are maintained in English.
- The scenic style contract applies to both production-oriented and vector-ready generation modes.
