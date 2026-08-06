# AI System Architect

Internal accelerator: turn a vague AI use case into a structured architecture draft and explicit assumptions.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

uv sync
uv sync --extra dev   # optional: pytest, ruff
```

## Usage

```bash
uv run architect --help
uv run architect version
uv run architect generate -d "My use case here"
uv run architect   # interactive: prompts for your use case
```

## Project layout

```
src/ai_system_architect/
  cli/          Typer entrypoints
  config/       Environment-backed settings
  core/         Logging, shared exceptions
  llm/          OpenAI client wiring (no prompts yet)
  services/     Application use cases (to be implemented)
tests/
```

## Development

```bash
uv run ruff check src tests
uv run pytest
```
