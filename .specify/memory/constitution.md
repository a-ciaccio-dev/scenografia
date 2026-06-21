<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
	- Template principle slot 1 -> I. Python-First Architecture
	- Template principle slot 2 -> II. Mandatory Local Virtual Environment
	- Template principle slot 3 -> III. Secret Management
	- Template principle slot 4 -> IV. Reproducible Output
	- Template principle slot 5 -> V. Output Folder Discipline
	- added VI. Scenic Style Contract
	- added VII. Agentic Architecture
	- added VIII. Human Confirmation Gate
	- added IX. Repository Discipline
- Added sections:
	- Operational Constraints
	- Workflow Gates
- Removed sections:
	- None
- Templates requiring updates:
	- ✅ .specify/templates/plan-template.md
	- ✅ .specify/templates/spec-template.md
	- ✅ .specify/templates/tasks-template.md reviewed; no change required because task generation remains blocked by Principle VIII
- Follow-up TODOs:
	- None
-->

# Scenografia Constitution

## Core Principles

### I. Python-First Architecture
The application MUST be implemented in Python. All planning and implementation
artifacts MUST prefer Python-native structure, tooling, and idioms over mixed-stack
or polyglot designs unless a later amendment explicitly approves an exception.
Code produced from this constitution MUST be modular, readable, and testable, with
clear separation between CLI orchestration, agent responsibilities, reusable tools,
and data models. Rationale: the first release is a Python CLI and architectural
drift away from Python would break both maintainability and delivery scope.

### II. Mandatory Local Virtual Environment
All Python dependencies MUST be installed inside `.venv` in the repository root.
Global Python package installations MUST NOT be used for application dependencies,
development dependencies, or runtime tooling that affects the project. Project
configuration MUST prefer `pyproject.toml` so dependency intent is explicit and
reproducible. Rationale: local isolation prevents environment drift and keeps the
project portable across machines and contributors.

### III. Secret Management
Secrets MUST NOT be hardcoded in source files, tests, scripts, prompts, or sample
artifacts. `OPENROUTER_API_KEY` MUST be loaded from `.env` or an equivalent local
environment source, and `.env` MUST NEVER be committed. A `.env.example` file MUST
exist without real secrets and MUST document required variables including
`OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `APP_INPUT_DIR`, `APP_OUTPUT_DIR`, and
the configurable image model identifier. Rationale: API key exposure would create an
immediate security and cost risk.

### IV. Reproducible Output
Every generation run MUST persist enough artifacts to reconstruct what happened.
At minimum each run MUST save the final image, final prompt, negative prompt,
structured brief, generation metadata, validation report, and processed sketch when
applicable. These artifacts MUST be written in stable, inspectable formats so future
operators can audit decisions and replay runs where feasible. Rationale:
reproducibility is essential for debugging model behavior, validating artistic
constraints, and comparing prompt or preprocessing changes.

### V. Output Folder Discipline
All generated results MUST be saved under `output/`. Each generation MUST use a
timestamped, human-readable subfolder name so operators can locate runs without
opening metadata first. No generation flow may silently write final outputs outside
the configured output root. Rationale: disciplined output storage prevents artifact
loss and keeps CLI runs operationally inspectable.

### VI. Scenic Style Contract
Every generated image MUST comply with the scenic artwork contract: full color,
solid fills, hand-drawn or hand-painted theatrical scenic look, no gradients, no
digital glow, no airbrush effects, clean outlines, closed paths where visually
possible, and layer separation in mind for future SVG export. Every prompt-building
or validation step MUST reinforce suitability for SVG vectorization, scenic
printing, digital projection, theatrical set design, and digital composition.
Outputs MUST also exclude photorealism, 3D-render aesthetics, blurry edges, text,
logos, watermarks, excessive micro-details, and unreadable shape noise. Rationale:
the product exists to generate production-usable scenic concepts rather than generic
AI illustrations.

### VII. Agentic Architecture
The application MUST be designed as a pipeline of agents and reusable tools.
Each agent MUST have exactly one clear operational responsibility, such as input
routing, sketch preprocessing, prompt composition, generation orchestration,
validation, or artifact persistence. Shared tools MUST be reusable, directly
testable, and callable independently of the top-level CLI. Rationale: the project
goal is not only image generation but a maintainable AI-agent workflow that can be
iterated without entangling responsibilities.

### VIII. Human Confirmation Gate
The workflow MUST stop after Constitution, Specification, and Plan until the user
explicitly authorizes the next phase. No `tasks`, implementation work, commit, or
push may be performed before that confirmation. Any automation that would continue
beyond planning MUST be disabled, skipped, or surfaced to the user for explicit
approval. Rationale: planning is an approval boundary, not a silent transition into
execution.

### IX. Repository Discipline
Existing files MUST NOT be overwritten without first reporting the risk and the
expected impact. When commits are later approved, commit messages MUST be clear and
traceable to the planning artifacts or implementation changes they represent. No
push to a remote repository is permitted before explicit confirmation. Rationale:
the repository is the audit trail for specification-driven work and must preserve
user control over destructive or externally visible actions.

## Operational Constraints

Spec Kit artifacts for this project MUST be written in English. The sketch strategy
for the initial product line is Hybrid: local preprocessing is the baseline, and any
later AI-assisted interpretation step must remain subordinate to reproducible local
artifacts and explicit configuration. The OpenRouter image model identifier MUST be
configurable through `.env`, CLI arguments, or both; it MUST NOT be hardcoded until
the project intentionally ratifies a specific Nano Banana model ID.

The first release target is a CLI application. Planning MUST prefer the smallest
viable architecture that satisfies the pipeline and artifact requirements without
premature service decomposition, background orchestration, or non-Python runtime
dependencies.

## Workflow Gates

All implementation plans MUST pass these gates before execution work begins:

1. Python gate: the chosen architecture stays Python-first and CLI-first.
2. Environment gate: `.venv`, `pyproject.toml`, `.env`, and `.env.example` are part
	 of the plan and no global dependency strategy is introduced.
3. Secret gate: API credentials are environment-driven and excluded from version
	 control.
4. Artifact gate: the plan includes stable storage for every required output asset.
5. Style gate: the scenic contract is enforced in prompt construction and validation.
6. Agent gate: each agent or tool has a named responsibility and test seam.
7. Approval gate: tasks, implementation, commit, and push remain blocked until the
	 user approves proceeding.

## Governance

This constitution supersedes conflicting local habits, prompts, or ad hoc planning
choices for the Scenografia project. Amendments MUST document the rationale,
affected workflow consequences, and any migration required for existing artifacts.

Versioning policy follows semantic versioning for governance:

- MAJOR: removing or materially redefining a principle in a backward-incompatible way.
- MINOR: adding a new principle, section, or materially expanded mandatory guidance.
- PATCH: clarifications, wording improvements, and non-semantic refinements.

Compliance review expectations:

- Every specification MUST reference this constitution implicitly through its scope
	and constraints.
- Every implementation plan MUST include an explicit constitution check against the
	workflow gates above.
- Reviews MUST reject plans or changes that violate `.venv` isolation, secret
	handling, output reproducibility, scenic style constraints, or the human
	confirmation gate.
- If a principle cannot be satisfied, the work MUST stop and the exception MUST be
	resolved by amendment or explicit user direction before execution continues.

**Version**: 1.0.0 | **Ratified**: 2026-06-21 | **Last Amended**: 2026-06-21
