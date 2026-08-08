# Manual Test Examples

Use these commands from the repo root.

## What is already covered by automated tests

- Happy path: `tests/test_generate.py::test_generate_architecture_returns_markdown`
- Minimal input path: `tests/test_generate.py::test_cli_default_invokes_generate_prompt`
- Empty input rejection: `tests/test_generate.py::test_generate_architecture_rejects_blank`
- Broken LLM output: `tests/test_generate.py::test_generate_architecture_rejects_invalid_output`

## What is still worth testing manually

These are the ones that benefit most from a live CLI run:

- Invalid enum input
- Approved stack cleanup with repeated or messy values
- End-to-end happy path against the real model

## 1. Happy path

Validates the full CLI-to-LLM flow.

```bash
uv run architect generate \
  -d "Internal support copilot for policy lookup, FAQ answers, and ticket triage" \
  --deployment-target Cloud \
  --data-sensitivity Internal \
  --scale Team \
  --approved-stack FastAPI \
  --approved-stack Postgres
```

Expected:

- prints the request payload first
- generates architecture markdown
- does not show validation errors

## 2. Minimal input

Validates defaults.

```bash
uv run architect generate -d "Simple invoice helper"
```

Expected:

- `deployment_target: Unsure`
- `data_sensitivity: Unsure`
- `scale: Unsure`
- `approved_stack: none`

## 3. Empty input

Validates CLI rejection before the model is called.

```bash
uv run architect generate
```

Then press Enter at the prompt.

Expected:

- `Description cannot be empty.`
- exit code `1`

## 4. Invalid enum

Validates request parsing.

```bash
uv run architect generate \
  -d "Invoice processor" \
  --deployment-target Foo
```

Expected:

- Typer rejects the value before any LLM call
- the error should list the allowed values

## 5. Approved stack repeated or messy

Validates normalization and cleanup.

```bash
uv run architect generate \
  -d "Customer support copilot" \
  --approved-stack " FastAPI " \
  --approved-stack "" \
  --approved-stack "Postgres" \
  --approved-stack "  "
```

Expected:

- `approved_stack: FastAPI, Postgres`
- blank entries are removed
- surrounding spaces are trimmed

## 6. Broken LLM output

Validates fail-closed behavior.

This is easiest to test as a unit test:

```bash
uv run pytest tests/test_generate.py -k rejects_invalid_output
```

Expected:

- the validator raises `OutputValidationError`
- partial markdown is not treated as success

## Suggested order

If you want the shortest learning path, run them in this order:

1. Minimal input
2. Empty input
3. Invalid enum
4. Approved stack cleanup
5. Happy path
6. Broken LLM output test
