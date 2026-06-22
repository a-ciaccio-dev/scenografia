# Scenografia: Codebase Architecture & Developer Guide

This document provides a comprehensive overview of the Scenografia project for AI agents and developers.

## 1. ARCHITECTURE & COMPONENTS

### High-Level Flow

```
User Input (CLI or Web UI)
  ↓
[Orientation Validation] ← Required before generation
  ↓
[BriefAgent] → Normalize to StructuredBrief
  ↓
[SketchInterpreterAgent] ← Only for sketch mode
  ↓
[PromptEngineerAgent] → Final prompt + negative prompt
  ↓
[ImageGenerationAgent] → Call OpenRouter chat/completions
  ↓
[StyleComplianceAgent] → Validate style & orientation
  ↓
[OutputManager] → Persist artifacts in timestamped folder
```

### Entry Points

- **CLI** (`src/scenografia/main.py`): Command-line interface using Typer for automated workflows and scripting
- **Web UI** (`src/scenografia/web_app.py`): Streamlit local web interface for interactive generation (optional dependency)

Both entry points orchestrate the same pipeline agents and services, ensuring consistent results.

### Core Components

#### **Agents** (`src/scenografia/agents/`)
Five specialized agents handle distinct workflow stages:

1. **BriefAgent** (`brief_agent.py`)
   - **Input**: GenerationRequest (text or sketch)
   - **Output**: StructuredBrief (dict with scene_description, constraints, guidance)
   - **Pattern**: Simple composition from templates; no external calls
   - **Key Methods**: `create_from_text()`, `create_from_sketch()`

2. **SketchInterpreterAgent** (`sketch_interpreter_agent.py`)
   - **Input**: GenerationRequest + output directory
   - **Output**: SketchInterpretation (processed image path, scene elements, composition notes)
   - **Pattern**: Local preprocessing first (OpenCV), optional AI refinement via callback
   - **Key Methods**: `interpret()`
   - **Note**: AI refinement is injected via callback, not called directly (testability)

3. **PromptEngineerAgent** (`prompt_engineer_agent.py`)
   - **Input**: StructuredBrief
   - **Output**: PromptPackage (final_prompt, negative_prompt, orientation_applied flag)
   - **Pattern**: Composes prompts using templates with scenic style constraints
   - **Key Methods**: `build_prompt_package()`

4. **ImageGenerationAgent** (`image_generation_agent.py`)
   - **Input**: GenerationRequest + PromptPackage + StructuredBrief
   - **Output**: ImageGenerationResponse (bytes + metadata)
   - **Pattern**: Orchestrates TextGenerationService and SketchGenerationService
   - **Key Methods**: `generate()`, lazily instantiates OpenRouterClient
   - **Note**: Both services handle end-to-end orchestration including artifact persistence

5. **StyleComplianceAgent** (`style_compliance_agent.py`)
   - **Input**: Brief + PromptPackage + Response (or file paths for validation)
   - **Output**: ValidationReport
   - **Pattern**: Validates scenic style contract, orientation capture, artifact completeness
   - **Key Methods**: `validate_text_run()`, `validate_run_folder()`, `validate_image_path()`

#### **Tools** (`src/scenografia/tools/`)
Reusable, stateless utilities:

1. **OpenRouterClient** (`openrouter_client.py`)
   - **Pattern**: Thin HTTP wrapper using httpx
   - **Key Methods**: `generate_image()`
   - **Critical Detail**: Uses `chat/completions` endpoint with `modalities=["image", "text"]` (not `/images/generations`)
   - **Orientation Mapping**: Maps Orientation enum to aspect ratio (16:9 for landscape, 9:16 for portrait, 1:1 for square)

2. **OutputManager** (`output_manager.py`)
   - **Pattern**: Static methods for timestamped directory creation and artifact persistence
   - **Key Methods**: 
     - `create_output_directory()` → Returns Path with slug format: `YYYY-MM-DD_HHMM_scene-slug`
     - `persist_text_run()` → Writes all artifacts and returns paths dict
     - `save_json_artifact()`, `save_text_artifact()`, `save_image_artifact()`
   - **Critical**: Atomicity and consistency of artifact writes

3. **PromptTemplates** (`prompt_templates.py`)
   - **Pattern**: Functions that build scenic constraint text
   - **Key Components**:
     - `SCENIC_STYLE_REQUIREMENTS` - Full color, hand-drawn look, clean outlines, SVG-ready
     - `SCENIC_STYLE_PROHIBITIONS` - Photorealism, gradients, text, watermarks, etc.
     - `build_final_prompt()` - Combines base prompt, orientation guidance, and style rules
     - `build_negative_prompt()` - Applies prohibitions

4. **StyleValidator** (`style_validator.py`)
   - **Pattern**: Static methods for validation rules
   - **Key Methods**: 
     - `validate_style_contract()` - Checks prompt includes scenic requirements
     - `validate_negative_constraints()` - Checks negative prompt includes prohibitions
     - `validate_artifact_completeness()` - Checks output folder has required files

5. **ImagePreprocessor** (`image_preprocessor.py`)
   - **Pattern**: Sketch preprocessing using OpenCV/numpy
   - **Key Methods**: `load_sketch()`, `preprocess_sketch()`, `extract_sketch_elements()`

6. **Config** (`config.py`)
   - **Pattern**: Singleton-like class with classmethod initialization
   - **Key Methods**: `initialize()`, `get_model_id()`, `validate()`
   - **Critical**: Loads from `.env` on module import, raises ValueError if OPENROUTER_API_KEY missing

#### **Schemas** (`src/scenografia/schemas/`)
Pydantic models for type safety:

1. **GenerationSchema** (`generation_schema.py`)
   - `GenerationMode` (draft, standard, production, vector-ready)
   - `Orientation` (portrait, landscape, square)
   - `GenerationRequest` (captures user intent)
   - `ImageGenerationResponse` (API response)

2. **ValidationSchema** (`validation_schema.py`)
   - `GenerationMetadata` (complete run record)
   - `ValidationReport` (style/orientation/artifact checks)

3. **BriefSchema**, **SketchSchema**, **GenerationSchema** → Domain model validation

#### **CLI Entry Point** (`main.py`)
- Uses `typer` for command structure
- Three commands: `generate`, `validate`, `models`
- **Critical Pattern**: Orientation is resolved interactively if missing via `_resolve_orientation()` → `_parse_orientation()`

#### **Services** (within ImageGenerationAgent)
Two orchestration services encapsulate end-to-end workflows:

1. **TextGenerationService**
   - Orchestrates: BriefAgent → PromptEngineerAgent → ImageGenerationAgent → StyleComplianceAgent → OutputManager
   - Returns dict with all artifact paths
   - **Note**: Has try/except to handle both old and new OutputManager signatures

2. **SketchGenerationService**
   - Orchestrates: BriefAgent → SketchInterpreterAgent → PromptEngineerAgent → ImageGenerationAgent → StyleComplianceAgent → OutputManager
   - Includes processed sketch in output dict

---

## 2. KEY PATTERNS

### Pattern 1: Dependency Injection via Constructor
All agents accept optional dependencies:
```python
class TextGenerationService:
    def __init__(
        self,
        brief_agent: BriefAgent | None = None,
        prompt_engineer: PromptEngineerAgent | None = None,
        # ...
    ):
        self.brief_agent = brief_agent or BriefAgent()
```
**Purpose**: Enables mocking in tests while keeping defaults simple.

### Pattern 2: Lazy Instantiation for Provider Calls
```python
def _get_image_generator(self) -> ImageGenerationAgent:
    """Instantiate the provider agent lazily for testability."""
    if self.image_generator is None:
        self.image_generator = ImageGenerationAgent()
    return self.image_generator
```
**Purpose**: Avoids expensive instantiation (HTTP client setup) during tests.

### Pattern 3: Pydantic Models for Type Safety & Validation
All domain objects are Pydantic BaseModel:
- Auto validation on instantiation
- JSON serialization via `.model_dump()` and `.model_dump(mode="json")`
- Field descriptions for API clarity

### Pattern 4: Enum-Driven Configuration
```python
class GenerationMode(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    # ...
```
- String enums for CLI and JSON compatibility
- Config maps modes to model IDs: `OPENROUTER_DRAFT_MODEL`, `OPENROUTER_STANDARD_MODEL`, etc.

### Pattern 5: Static Methods for Stateless Operations
OutputManager, StyleValidator use static methods:
```python
@staticmethod
def create_output_directory(scene_slug: str) -> Path:
```
**Purpose**: Emphasizes no state; can be called without instantiation.

### Pattern 6: Aspect Ratio as Orientation Proxy
Orientation enum is passed through entire pipeline and mapped to aspect ratio only at provider call:
```python
aspect_ratio = self._map_orientation_to_aspect_ratio(orientation)
```
**Purpose**: Keeps orientation concern orthogonal from API specifics.

### Pattern 7: Dict-Based Brief Exchange
Agents exchange briefs as dicts (not strict types) for flexibility:
```python
brief = {
    "scene_description": "...",
    "orientation": Orientation.LANDSCAPE,
    "style_constraints": [...],
    # ...
}
```
**Purpose**: Allows forward evolution without schema versioning.

### Pattern 8: Timestamped Human-Readable Directories
Output folder naming: `YYYY-MM-DD_HHMM_scene-slug`
- Timestamp sorts chronologically
- Scene slug is human-readable
- Uniqueness guaranteed by minute granularity + slug

### Pattern 9: CLI-Only Interactive Fallback
```python
def _resolve_orientation(orientation: Optional[str]) -> Orientation:
    if orientation is not None:
        return _parse_orientation(orientation)
    selected = typer.prompt("Orientation (portrait, landscape, square)")
    return _parse_orientation(selected)
```
**Purpose**: Supports both non-interactive (automation) and interactive (local CLI) use.

### Pattern 10: Try/Except for Backward Compatibility
Services have try/except for old OutputManager signature:
```python
try:
    return self.output_manager.persist_text_run(brief=brief, ...)
except TypeError:
    return self.output_manager.persist_text_run(brief, ...)
```
**Purpose**: Graceful migration during API refinement (but should be cleaned up).

---

## 3. BUILD, TEST, RUN COMMANDS

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate   # macOS/Linux

# Install editable mode (includes dev dependencies)
pip install -e ".[dev]"

# Create .env (required for live generation)
copy .env.example .env
# Edit .env with OPENROUTER_API_KEY
```

### Running

**Text generation** (requires OPENROUTER_API_KEY in .env):
```bash
python -m scenografia generate \
  --prompt "fairytale medieval village with a castle" \
  --mode standard \
  --orientation landscape
```

**Sketch generation**:
```bash
python -m scenografia generate \
  --sketch input/sketches/sketch.png \
  --style "steampunk interior wall" \
  --mode vector-ready \
  --orientation portrait \
  --disable-ai-refinement  # optional
```

**Validation**:
```bash
python -m scenografia validate --image output/2026-06-22_1032_example/final.png
python -m scenografia validate --run output/2026-06-22_1032_example
```

**List models**:
```bash
python -m scenografia models
```

### Testing

```bash
# Run all tests with coverage
pytest -v --cov=src/scenografia --cov-report=term-missing

# Run specific test file
pytest tests/test_generate_cli.py -v

# Run specific test
pytest tests/test_generate_cli.py::test_generate_text_happy_path -v

# Run tests matching pattern
pytest -k "orientation" -v

# Generate coverage report
pytest --cov=src/scenografia --cov-report=html
# Open htmlcov/index.html in browser
```

### Linting & Formatting
(Not explicitly configured in pyproject.toml, but should be added):
```bash
# Example if using pylint/flake8:
pylint src/scenografia tests

# Example if using black:
black src/scenografia tests --check
```

---

## 4. DEVELOPMENT WORKFLOW FOR AI AGENTS

### Before Making Changes
1. **Understand the orientation flow**: Orientation must thread through CLI → Request → Brief → Prompt → Metadata. Check all five places.
2. **Identify the agent responsibility**: Is this a concern of BriefAgent, PromptEngineer, StyleValidator, or OutputManager?
3. **Check existing tests**: Look at `tests/` to understand testing patterns before adding new features.
4. **Run full test suite**: Ensure baseline passes before making changes.

### Making Changes
1. **Modify the agent or tool** with its single responsibility in mind.
2. **Update related Pydantic schemas** if data structures change.
3. **Add or update tests** before committing (TDD preferred).
4. **Test locally**:
   ```bash
   # Test the specific module
   pytest tests/test_<module>.py -v
   
   # Run full suite
   pytest -v --cov=src/scenografia --cov-report=term-missing
   ```
5. **Manual CLI validation** (if environment allows):
   ```bash
   python -m scenografia generate --prompt "test" --mode standard --orientation landscape
   ```

### Testing Patterns

**Stub Pattern** (used in CLI tests):
```python
class StubGenerationService:
    def __init__(self):
        self.calls = []
    def run_text_generation(self, ...):
        self.calls.append({...})
        return {"output_dir": Path("output/run-001"), ...}

def test_generate_text(monkeypatch):
    service = StubGenerationService()
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: service)
    result = runner.invoke(app, [...])
    assert service.calls[0]["orientation"] == Orientation.LANDSCAPE
```

**Fixture Pattern** (for reusable test data):
```python
# tests/fixtures/ contains sketch_dummy.png and other test assets
```

**Mock Pattern** (for external calls):
```python
# Use unittest.mock or pytest fixtures to mock OpenRouterClient
```

---

## 5. COMMON PITFALLS & WHAT TO WATCH FOR

### Pitfall 1: Orientation Not Threading Through
**Mistake**: Modifying BriefAgent without updating PromptEngineerAgent to use brief["orientation"]
**Fix**: Always trace: CLI option → GenerationRequest.orientation → brief["orientation"] → prompt text → validation report
**Check**: Search for "orientation" in prompt_templates.py and validation_schema.py

### Pitfall 2: Forgetting to Persist Orientation in Artifacts
**Mistake**: Validation report created without orientation field
**Fix**: StyleComplianceAgent.validate_text_run() must capture brief["orientation"]
**Check**: ValidationReport model requires orientation field (Pydantic enforces this)

### Pitfall 3: Adding Scenic Constraints Without Updating Prohibitions
**Mistake**: Adding a requirement like "must include gold leaf" without updating negative constraints
**Fix**: Keep SCENIC_STYLE_REQUIREMENTS and SCENIC_STYLE_PROHIBITIONS in sync in prompt_templates.py
**Check**: Any change to scenic rules must update both build_final_prompt() and build_negative_prompt()

### Pitfall 4: Breaking Config Initialization
**Mistake**: Accessing Config.OPENROUTER_API_KEY before Config.initialize() is called
**Fix**: Config.initialize() is called on module import (see config.py bottom), but tests should mock Config
**Check**: If test fails with "OPENROUTER_API_KEY not set", ensure test mocks Config or provides .env

### Pitfall 5: Artifact Persistence Race Conditions
**Mistake**: Writing brief.json before final.png completes
**Fix**: OutputManager.persist_text_run() writes all artifacts before returning paths dict
**Check**: Validate that all files exist before finalize_validation_report() is called

### Pitfall 6: Mixing Bytes vs. PIL Image Objects
**Mistake**: Passing PIL Image to OpenRouterClient when it expects base64 bytes
**Fix**: ImageGenerationResponse.image_data is bytes; convert in client if needed
**Check**: OpenRouterClient.generate_image() expects prompt (string); handles response deserialization

### Pitfall 7: Orientation Enum Serialization
**Mistake**: JSON serialization fails because Orientation is a Python enum
**Fix**: Orientation is `str, Enum` subclass, so `.value` works and JSON serialization is automatic
**Check**: ValidationReport.model_dump(mode="json") must handle Orientation.PORTRAIT → "portrait"

### Pitfall 8: Sketch Preprocessing Silent Failures
**Mistake**: SketchPreprocessor returns None without clear error propagation
**Fix**: Always check return value and raise ValueError with context
**Check**: SketchInterpreterAgent.interpret() validates: `if original_image is None or processed_image is None: raise ValueError(...)`

### Pitfall 9: Tests Pass Locally, Fail in CI
**Mistake**: Tests depend on .env file or hardcoded model IDs
**Fix**: Mock Config.OPENROUTER_API_KEY and OpenRouterClient entirely in tests
**Check**: Test files should not require real .env or API calls

### Pitfall 10: Old Brief Schema Compatibility
**Mistake**: Assuming brief dict keys exist when BriefAgent evolves schema
**Fix**: Use .get() with defaults and update all consumers when adding required fields
**Check**: brief.get("style_guidance", "") is safer than brief["style_guidance"]

---

## 6. CRITICAL FILES & PATTERNS TO PRESERVE

### Must Not Break These Contracts

| File | Why Critical | Contract |
|------|-------------|----------|
| `schemas/generation_schema.py` | Defines Orientation, GenerationMode | Always include exactly 3 orientations; GenerationMode must remain string enum |
| `config.py` | Initialization and model mapping | Config.initialize() on import; OPENROUTER_API_KEY is mandatory |
| `main.py` | CLI surface | generate, validate, models commands; orientation is mandatory input |
| `agents/brief_agent.py` | Data normalization | Always returns dict with scene_description, orientation, style_constraints |
| `tools/prompt_templates.py` | Scenic style rules | SCENIC_STYLE_REQUIREMENTS and SCENIC_STYLE_PROHIBITIONS must stay in sync |
| `tools/output_manager.py` | Artifact atomicity | All files written before returning; folder naming YYYY-MM-DD_HHMM_slug |
| `schemas/validation_schema.py` | Validation report schema | Must include orientation_valid, style_contract_applied, artifacts_complete |

### Evolve These With Care

| File | Stability | Notes |
|------|-----------|-------|
| `agents/image_generation_agent.py` | Moderate | TextGenerationService and SketchGenerationService are orchestration entry points; lazy initialization of ImageGenerationAgent is key pattern |
| `tools/openrouter_client.py` | Low | Currently expects chat/completions with modalities=[image]; if provider changes, entire mapping layer must update |
| `agents/style_compliance_agent.py` | Moderate | Validation rules (StyleValidator calls) should remain independent; can add new rules without breaking existing ones |
| `agents/sketch_interpreter_agent.py` | Low | Refinement callback pattern is testable but inflexible; consider refactor if AI vision needs become more complex |

### Test These Thoroughly

- **Orientation threading**: Add a test that traces orientation from CLI → final artifact
- **Config initialization**: Test that Config.initialize() handles missing OPENROUTER_API_KEY
- **Artifact persistence**: Test that all output files are written before OutputManager.persist_text_run() returns
- **Validation report**: Test that ValidationReport captures all fields correctly
- **CLI argument parsing**: Test all combinations of --prompt, --sketch, --mode, --orientation

---

## 7. ARCHITECTURE DECISIONS & RATIONALE

### Why Agents + Services?
- **Agents** (BriefAgent, PromptEngineerAgent, etc.) handle domain concerns and are testable in isolation
- **Services** (TextGenerationService, SketchGenerationService) orchestrate the full pipeline and handle error recovery
- Separation allows evolving each agent independently

### Why Dict-Based Brief Exchange?
- Briefs are large, multi-field objects that change as the workflow evolves
- Pydantic for type safety at entry/exit points; dicts for internal flexibility
- Avoids rigid schema lock-in during rapid feature development

### Why Orientation is a Mandatory First-Class Citizen?
- Spec requires orientation capture before generation (FR-005, FR-008)
- Threaded through every component for auditability and reproducibility
- Enables aspect ratio mapping at provider level without CLI coupling

### Why Timestamped Human-Readable Output Folders?
- Timestamp ensures chronological sorting and uniqueness
- Human-readable slug allows quick identification without opening metadata
- Atomic write of all artifacts in one folder enables easy backup/replay

### Why Lazy Instantiation of ImageGenerationAgent?
- OpenRouterClient setup involves HTTP client initialization (expensive)
- Tests can mock without triggering real API calls
- Pattern enables graceful testing of orchestration without provider dependencies

---

## 8. NEXT STEPS FOR EXTENDING

### To Add a New Input Mode (e.g., video → scenic frame):
1. Add new input type to GenerationRequest schema
2. Add create_from_video() to BriefAgent
3. Add new service VideoGenerationService in image_generation_agent.py
4. Add CLI command option for video path
5. Add corresponding tests

### To Add a New Generation Mode (e.g., "experimental"):
1. Add to GenerationMode enum in generation_schema.py
2. Add config entry OPENROUTER_EXPERIMENTAL_MODEL in config.py
3. Add corresponding test in test_generate_cli.py
4. Update README.md

### To Add a New Validation Rule:
1. Add check function to StyleValidator in style_validator.py
2. Call from StyleComplianceAgent.validate_text_run()
3. Add result field to ValidationReport
4. Add test in test_validation_workflow.py

### To Migrate to a Different Image Provider:
1. Create new client class (e.g., ReplicateClient) inheriting from OpenRouterClient interface
2. Update ImageGenerationAgent to accept client parameter
3. Update Config to load provider-specific model IDs
4. Update tests to mock new client
5. Preserve Orientation → aspect ratio mapping layer

---

## 9. DEBUGGING TIPS

### "Image generation returns None"
- Check: Did OpenRouterClient.generate_image() get a valid model ID?
- Check: Does model_id support `output_modalities=image` on your OpenRouter account?
- Check: Is OPENROUTER_API_KEY set correctly in .env?

### "Orientation not in output"
- Search for "orientation" in validation_report.json and generation_response.json
- Trace: Does BriefAgent.create_from_text() include orientation in brief dict?
- Trace: Does PromptEngineerAgent.build_prompt_package() set orientation_applied flag?

### "Validation fails but image looks correct"
- Check: Does validation_report.json show style_contract_applied == true?
- Check: Are all required files present in output folder?
- Check: Does negative_prompt.txt include photorealism/gradients prohibitions?

### "Tests pass locally, fail in CI"
- Mock Config.OPENROUTER_API_KEY instead of relying on .env
- Mock OpenRouterClient instead of making real API calls
- Use CliRunner from typer.testing instead of subprocess

