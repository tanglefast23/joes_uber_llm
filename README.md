# Joe's Uber LLM

A web interface for chatting with multiple LLM providers using your own API keys.

## Features

- Support for OpenAI, Anthropic, and Google Gemini models
- Clean, responsive web interface with HTMX
- API keys stored locally in browser (never on server)
- Conversation history per session

## Installation

```bash
uv venv
uv pip install -e ".[dev]"
```

## Usage

```bash
uv run uvicorn src.joes_uber_llm.main:app --reload
```

Open http://localhost:8000 in your browser.

## Supported Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| Anthropic | claude-sonnet-4-20250514, claude-3-5-haiku-20241022, claude-opus-4-20250514 |
| Google | gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp |

## Development

Run tests:
```bash
uv run pytest tests/ -v
```

Run linting:
```bash
uv run ruff check .
uv run ruff format .
```

Run type checking:
```bash
uv run mypy src/
```
