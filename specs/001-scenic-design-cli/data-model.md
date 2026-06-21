# Data Model: AI Scenic Design CLI

## Orientation

**Purpose**: Normalized aspect intent collected before generation.

**Fields**:
- `value`: enum, required, one of `portrait`, `landscape`, `square`

**Validation Rules**:
- Must be present before image generation starts.
- Must reject any value outside the enum.
- May be collected through `--orientation` or through an interactive CLI prompt.

## Generation Request

**Purpose**: Canonical runtime input passed into the agent pipeline.

**Fields**:
- `input_mode`: enum, required, `text` or `sketch`
- `prompt`: string, optional when `input_mode=sketch`, required when `input_mode=text`
- `sketch_path`: path string, optional when `input_mode=text`, required when `input_mode=sketch`
- `style_guidance`: string, optional
- `generation_mode`: enum, required, `draft`, `standard`, `production`, `vector-ready`
- `orientation`: `Orientation`, required
- `model_id_override`: string, optional
- `ai_refinement_enabled`: boolean, required for sketch mode decision-making

**Relationships**:
- Produces one `Structured Brief`
- Produces one `Prompt Package`
- Produces one `Generation Metadata`

**Validation Rules**:
- Exactly one of `prompt` or `sketch_path` must define the primary input mode.
- Orientation must be valid before downstream agents run.

## Sketch Interpretation

**Purpose**: Structured result of local sketch preprocessing plus optional AI refinement.

**Fields**:
- `source_sketch_path`: path string, required
- `processed_sketch_path`: path string, required after preprocessing
- `local_features`: object, required
- `ai_refinement_summary`: string, optional
- `scene_description`: string, required

**Validation Rules**:
- Local preprocessing always precedes any AI refinement.
- `processed_sketch_path` is mandatory for sketch runs.

## Structured Brief

**Purpose**: Normalized scenic description used for prompt generation.

**Fields**:
- `scene_description`: string, required
- `orientation`: `Orientation`, required
- `generation_mode`: enum, required
- `style_constraints`: list of strings, required
- `negative_constraints`: list of strings, required
- `composition_guidance`: list of strings, required
- `input_source`: enum, required, `text` or `sketch`

**Relationships**:
- Derived from `Generation Request`
- May incorporate `Sketch Interpretation`
- Produces one `Prompt Package`

**Validation Rules**:
- Must include the scenic style contract.
- Must include orientation-aware composition intent.

## Prompt Package

**Purpose**: Final instruction set sent toward image generation.

**Fields**:
- `final_prompt`: string, required
- `negative_prompt`: string, required
- `orientation_applied`: boolean, required

**Validation Rules**:
- Final prompt must include scenic style constraints.
- Final prompt must include orientation intent.
- Negative prompt must encode all forbidden output traits.

## Provider Request Mapping

**Purpose**: Model-specific request payload generated from generic pipeline data.

**Fields**:
- `model_id`: string, required
- `prompt`: string, required
- `negative_prompt`: string, required when supported or internally preserved
- `orientation`: `Orientation`, required
- `provider_image_config`: object, optional

**Validation Rules**:
- If the target model supports aspect ratio or image configuration, orientation
  must be translated into provider-specific fields.
- If not supported, orientation remains encoded in the prompt.

## Generation Metadata

**Purpose**: Operational record of a generation run.

**Fields**:
- `run_id`: string, required
- `timestamp`: datetime string, required
- `input_mode`: enum, required
- `generation_mode`: enum, required
- `orientation`: `Orientation`, required
- `model_id`: string, required
- `ai_refinement_enabled`: boolean, required
- `artifact_paths`: object, required

**Validation Rules**:
- Must include saved orientation.
- Must reference all produced artifacts.

## Validation Report

**Purpose**: Compliance and completeness record for a run.

**Fields**:
- `run_id`: string, required
- `orientation`: `Orientation`, required
- `orientation_valid`: boolean, required
- `style_contract_applied`: boolean, required
- `negative_constraints_applied`: boolean, required
- `artifacts_complete`: boolean, required
- `issues`: list of strings, optional

**Validation Rules**:
- Must record whether orientation was captured and valid.
- Must record whether the scenic style contract and negative constraints were applied.
- Must verify artifact completeness for the selected input mode.

## State Transitions

1. `Generation Request` created
2. Orientation validated
3. `Sketch Interpretation` created when input mode is `sketch`
4. `Structured Brief` created
5. `Prompt Package` created
6. `Provider Request Mapping` created
7. Generation response received
8. `Generation Metadata` and `Validation Report` persisted