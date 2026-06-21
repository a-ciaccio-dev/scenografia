# Provider Adapter Contract: OpenRouter Image Generation

## Purpose

Translate generic pipeline data into an OpenRouter request while keeping model IDs
configurable and preserving orientation behavior.

## Inputs

- `model_id`
- `final_prompt`
- `negative_prompt`
- `orientation`
- optional provider-specific image configuration

## Behavioral Rules

- The adapter must accept a validated orientation value.
- If the selected model supports explicit aspect ratio or image configuration, the
  adapter must translate `portrait`, `landscape`, or `square` into the appropriate
  provider request field.
- If the selected model does not support explicit orientation or aspect ratio fields,
  the adapter must still preserve the orientation requirement by ensuring it remains
  encoded in the final prompt.
- The adapter must not hardcode the default model ID.
- The adapter must expose enough structured response data to persist
  `generation_response.json` and generation metadata.

## Open Questions Intentionally Deferred

- Exact OpenRouter request field name for aspect ratio or image size
- Exact Nano Banana model ID to configure by default
- Whether a separate OpenRouter vision model is used for optional sketch refinement