# AI System Architect

Draft an architecture from a use case description using the OpenAI Responses API.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cp .env.example .env

# Required
# OPENAI_API_KEY=your_api_key_here

# Optional
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

uv sync
uv sync --extra dev   # optional: pytest, ruff
```

## Configuration

The app reads configuration from `.env` and environment variables.

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | OpenAI API key used by the Responses API client |
| `OPENAI_BASE_URL` | No | Optional override for a compatible OpenAI endpoint |
| `OPENAI_MODEL` | No | Model used for architecture generation |
| `LOG_LEVEL` | No | Logging verbosity |
| `OUTPUT_DIR` | No | Directory for generated artifacts |

`OPENAI_BASE_URL` may be left empty, omitted, or set to a full URL like `https://api.openai.com/v1`.

## Usage

```bash
uv run architect --help
uv run architect version
uv run architect generate -d "Customer support chatbot for an IT firm"
uv run architect   # interactive: prompts for your use case
```

The CLI prints the generated markdown directly to stdout. No streaming is used.

## Input guidance

The generator intentionally asks for more detail when the brief is too short or underspecified.

If the use case is under roughly 15 meaningful words, or does not say:

- what the system does
- who uses it

the model returns a short clarification request instead of a generic architecture.

If you want it to proceed anyway, include the phrase `proceed anyway` in the prompt or give a fuller brief with the target users, tasks, and constraints.

## Project layout

```
src/ai_system_architect/
  cli/          Typer entrypoints
  config/       Environment-backed settings
  core/         Logging and shared exceptions
  llm/          OpenAI client wiring
  prompts/      System prompt used by the generator
  services/     Application use cases
tests/
```

## Development

```bash
uv run ruff check src tests
uv run pytest
```
