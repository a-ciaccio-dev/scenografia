# Scenografia: AI Agent Instructions

Scenografia is a theatrical scenic design CLI that generates and validates stage artwork from text prompts or sketches. This file guides AI agents on codebase conventions, critical patterns, and development workflow.

## 📋 Quick Reference

**Tech Stack**: Python 3.11+, Typer (CLI), Pydantic, httpx, OpenRouter API, Pillow, imageio

**Key Directories**:
- `src/scenografia/` — Main package
  - `agents/` — Orchestration logic (5 agents)
  - `tools/` — Reusable services (6 tools)
  - `schemas/` — Pydantic models (type contracts)
  - `main.py` — CLI entry point
- `specs/` — Design documents and planning
- `tests/` — Full test suite with ~87% coverage

**Essential Commands**:
```bash
# Setup
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
pip install -e .
cp .env.example .env  # Add OPENROUTER_API_KEY

# Development
python -m scenografia generate --prompt "..." --mode standard --orientation landscape
python -m scenografia.main validate --run output/FOLDER
python -m pytest tests/ -v

# Both CLI syntaxes work:
python -m scenografia models
python -m scenografia.main models
```

## 🏗️ Architecture

**High-Level Flow**: Text/Sketch → CLI → Agent Orchestration → OpenRouter API → Validated Output

**5 Agents**:
1. **BriefAgent** — Converts user input to structured brief
2. **PromptEngineer** — Builds theatrical-style prompts with scenic constraints
3. **SketchInterpreter** — Analyzes sketch images for design elements
4. **ImageGeneration** — Calls OpenRouter `/chat/completions` endpoint
5. **StyleCompliance** — Validates output against theatrical style contracts

**6 Tools**:
- **OpenRouterClient** — HTTP client for image generation via chat/completions
- **Config** — Environment-based configuration and model selection
- **OutputManager** — Atomic artifact persistence (JSON, images, text)
- **PromptTemplates** — Scenic constraint library and prompt assembly
- **StyleValidator** — Style compliance checks and artifact validation
- **ImagePreprocessor** — Sketch normalization and element detection

👉 **Full architecture details**: [ARCHITECTURE.md](ARCHITECTURE.md)

## 🎭 Critical Patterns & Contracts

**1. Orientation is Mandatory First-Class**
- Must thread through: CLI → GenerationRequest → StructuredBrief → PromptPackage → Metadata → ValidationReport
- Supported: `landscape` (16:9), `portrait` (9:16), `square` (1:1)
- Aspect ratio is derived from orientation for API calls

**2. Scenic Style is the Visual Contract**
- `SCENIC_STYLE_REQUIREMENTS` — Must include theatrical language (e.g., "stage-appropriate", "flat colors")
- `SCENIC_STYLE_PROHIBITIONS` — Must exclude photorealistic elements
- Both defined in `PromptTemplates` and must stay in sync with validation logic

**3. OpenRouter Image Generation**
- Endpoint: `https://openrouter.ai/api/v1/chat/completions` (POST)
- Payload: `model`, `messages`, `modalities: ["image", "text"]`, `image_config: {aspect_ratio}`, `stream: false`
- Response: Extract from `choices[0].message.images[0].image_url.url`
- Handles both base64 data URLs and remote URLs with proper error handling
- **Never expose OPENROUTER_API_KEY in error messages**

**4. Output Atomicity**
- All artifacts written together in `persist_text_run()` before returning paths
- Directory format: `YYYY-MM-DD_HHMM_scene-slug/`
- Never assume individual files exist independently

**5. Configuration is Lazy + Fallback-Driven**
```python
priority: CLI override → Env variable → Config.get_model_id() → Fallback default
```
- `Config.initialize()` must be called before any generation
- Fallback model: `google/gemini-2.5-flash-image` (all modes)

## ⚠️ Common Pitfalls & Prevention

| Pitfall | Impact | Prevention |
|---------|--------|-----------|
| Orientation not threading through pipeline | ValidationReport fails; can't trace where lost | Check all 5 agents; use grep to audit flow |
| Scenic constraints out of sync | Style validation inconsistent with prompt | Update BOTH build_final_prompt() AND build_negative_prompt() |
| Config not initialized | OPENROUTER_API_KEY KeyError at runtime | Call Config.initialize() once in main.py entry point |
| API key exposed in errors | Security risk; leaked to logs | Always catch exceptions; use message.format(sanitized=True) |
| Tests mock OpenRouterClient inconsistently | CI passes but prod fails | Use @patch decorator; verify .post() call args match |
| Bytes vs PIL Image mixing | TypeError in image processing | Use ImagePreprocessor._pil_to_bytes() for conversion |

## 🔧 Making Changes: Workflow

1. **Identify scope**: Which agent(s) or tool(s) does this touch?
2. **Check contracts**: Review the Pydantic schema changes needed (if any)
3. **Preserve orientation flow**: If modifying brief, request, or response, ensure orientation propagates
4. **Update validation logic**: If changing style rules, update both prompt AND validator
5. **Write tests first**: Use CliRunner for CLI tests; mock OpenRouterClient for unit tests
6. **Run full suite**: `pytest tests/ -v` must pass before committing
7. **Update docs**: Link to [ARCHITECTURE.md](ARCHITECTURE.md) section if complex

## 📚 Detailed References

- **Design Context**: [specs/001-scenic-design-cli/plan.md](specs/001-scenic-design-cli/plan.md)
- **Data Models**: [specs/001-scenic-design-cli/data-model.md](specs/001-scenic-design-cli/data-model.md)
- **Architecture & Patterns**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Full Requirements**: [specs/001-scenic-design-cli/spec.md](specs/001-scenic-design-cli/spec.md)

## 🆘 Quick Debugging

**"404 Not Found" on image generation**  
→ Verify OpenRouter endpoint is `/chat/completions` (not `/images/generations`)  
→ Check `modalities: ["image", "text"]` in request payload

**"OPENROUTER_API_KEY not found"**  
→ Ensure `.env` exists with valid key  
→ Verify `Config.initialize()` called before generation

**Orientation missing in output**  
→ Check StructuredBrief includes orientation  
→ Grep for orientation in ValidationReport building

**Test mocking failures**  
→ Verify mock target: `@patch('scenografia.tools.openrouter_client.httpx.Client')`  
→ Check mock.post() call matches actual payload structure

## 🚀 Next Steps for Agents

- Always start with `Config.initialize()` when touching configuration
- Use Pydantic model validation for all data boundaries
- Test both CLI syntaxes: `python -m scenografia` AND `python -m scenografia.main`
- Never hardcode model IDs; use `Config.get_model_id(mode, override)`
- Document why orientation/style changes affect multiple files
