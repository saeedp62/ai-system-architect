# AI System Architect

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)
[![CLI](https://img.shields.io/badge/Interface-CLI-orange)](#usage)

AI System Architect turns a rough use case into a structured architecture draft using the OpenAI Responses API.

## Overview

This project is a CLI tool for converting a short product idea into a practical system architecture. It is designed for engineers, founders, and technical teams who want a fast first-pass design with explicit assumptions, tradeoffs, and implementation guidance.

The generator is opinionated by design:

- It asks for more detail when the prompt is too vague
- It returns markdown directly to the terminal
- It uses the OpenAI Responses API with no streaming
- It loads configuration from `.env`

## Features

- Markdown architecture drafts generated from plain-language prompts
- OpenAI Responses API integration
- Environment-based configuration via `.env`
- Clear handling for empty input and provider errors
- CLI-first workflow with Typer
- Structured prompts that encourage explicit assumptions

## Architecture

The application is organized into a small set of focused layers:

- `cli/` handles the command-line interface and user interaction
- `config/` loads and normalizes environment settings
- `llm/` creates the OpenAI client
- `prompts/` stores the system prompt used for generation
- `services/` contains the architecture generation use case
- `core/` defines shared exceptions and logging helpers

Request flow:

1. The CLI collects a use case description.
2. `generate_architecture(user_input)` validates the input.
3. Settings are loaded from the environment.
4. The OpenAI client is created with the configured API key.
5. The system prompt and user input are sent through the Responses API.
6. The generated markdown is printed to stdout.

## Tech Stack

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Typer](https://typer.tiangolo.com/)
- [Rich](https://rich.readthedocs.io/)
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- Pytest
- Ruff

## Installation

```bash
git clone <your-repo-url>
cd AI-SYSTEM-ARCHITECT

cp .env.example .env

# Set your OpenAI API key
# OPENAI_API_KEY=your_api_key_here

uv sync
uv sync --extra dev
```

Optional environment variables:

```bash
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini
# LOG_LEVEL=INFO
# OUTPUT_DIR=./outputs
```

## Usage

```bash
uv run architect --help
uv run architect version
uv run architect generate -d "Customer support chatbot for an IT firm"
uv run architect
```

The interactive command prompts for a use case description. If the brief is too short or omits key details, the generator may ask for clarification instead of producing a generic architecture.

## Roadmap

- Add architecture export to files
- Add provider health checks and diagnostics
- Support structured inputs such as deployment target and scale
- Add evaluation and regression test workflows
- Add conversation memory and multi-step refinement

## Screenshots

```bash
$ uv run architect
Describe your AI application.: Customer support chatbot for an IT firm
Generating architecture...

# Architecture Draft

## 0. Assumptions
- The chatbot supports external customers and internal support staff.
- The first release focuses on FAQs and ticket deflection.

## 1. Problem Statement
...
```

Replace this block with real screenshots after you capture terminal output or add a UI later.

## License

This project is licensed under the [MIT License](https://opensource.org/license/mit/).
Add a `LICENSE` file to the repository when you are ready to publish formally.
