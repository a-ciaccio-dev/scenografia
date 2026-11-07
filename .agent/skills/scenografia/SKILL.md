---
name: scenografia
description: "Theatrical scenic design assistant for generating and validating stage backdrops (fondali teatrali) with SVG-safe constraints using Antigravity subagents and native pipelines."
---

# Scenografia — Theatrical Scenic Design Skill

Use this skill when the user wants to design, enhance, generate, or validate theatrical backdrops, stage designs, or scenographic concept sketches.

## Workflow Pipeline

When requested to create or refine a theatrical scenic design:

1. **Brief & Concept Normalization** (`BriefAgent`):
   - Determine the scene setting (e.g., Bosco medievale, Salone aristocratico, Paesaggio surreale).
   - Confirm required orientation:
     - `landscape` (default 16:9 for wide stages)
     - `portrait` (9:16 for vertical theatre scrims/banners)
     - `square` (1:1 for proscenium box miniatures)

2. **Prompt Enhancement & Theatrical Structuring** (`PromptEnhancerAgent`):
   - Rewrite user concept into structured scenic specifications with emojis:
     - 🎨 Dati Tecnici & Titolo
     - 📐 Composizione & Prospettiva
     - 🧱 Elementi Scenografici
     - 🎨 Palette Colori & Luci
   - Enforce SVG-safe rules:
     - Flat, solid fills with clean outlines
     - Closed vector paths
     - Strictly no photorealism, no digital airbrush, no gradient blur
     - No text, logos, or watermarks

3. **Generation & Orchestration**:
   - If running inside Antigravity:
     - Use the Antigravity `image-generator` subagent or `AntigravityBridgeProvider` to render the canvas.
   - If running via local CLI/services:
     - Run `python -m scenografia generate --prompt "<enhanced_prompt>" --orientation landscape --mode standard`

4. **Style Compliance & Validation** (`StyleComplianceAgent`):
   - Verify presence of scenic style indicators.
   - Check negative constraints compliance.
   - Validate artifact completeness (`final.png`, `prompt.txt`, `brief.json`, `validation_report.json`).
