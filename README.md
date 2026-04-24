# ChatMate

ChatMate is a small Python chat application built around the MVC paradigm.
It supports multiple LLM backends through `config.yaml` and `.env`:

- OpenAI
- Anthropic Claude
- LM Studio via an OpenAI-compatible local endpoint

## Features

- MVC-oriented project layout
- PySide6 desktop UI
- YAML-driven provider selection with `.env` secrets
- Automatic chat persistence
- Saved chat list with create, rename, load, and delete controls
- Shared chat history model

## Quick Start

1. Create your `.env` from the example and add tokens:

```bash
cp .env.example .env
```

2. Install dependencies with `uv`:

```bash
uv sync
```

3. Update `config.yaml` with the provider you want to use.
4. Start the desktop app:

```bash
uv run chatmate
```

You can also run:

```bash
uv run python main.py
```

## Environment Variables

Use `.env` for secrets:

```dotenv
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LMSTUDIO_API_KEY=lm-studio
```

## LM Studio Local Setup

To use a local model through LM Studio:

1. Start the LM Studio local server.
2. In `config.yaml`, set `provider.active: lmstudio`.
3. Set the LM Studio model id under `provider.lmstudio.model`.
4. Keep `provider.lmstudio.base_url` as `http://localhost:1234/v1` unless you changed the port.
5. Leave `LMSTUDIO_API_KEY=lm-studio` in `.env`, or any other non-empty value your local setup accepts.

Example:

```yaml
provider:
  active: lmstudio
  lmstudio:
    base_url: "http://localhost:1234/v1"
    model: "your-lm-studio-model-id"
```

## Chat UX

- Chats are auto-saved under `.chatmate/chats`
- The sidebar lets you create, rename, switch, and delete saved chats
- Press `Enter` to send the current message
- Press `Shift+Enter` to insert a new line in the message box

## Configuration

`config.yaml` stores non-secret settings such as the active provider, models,
and LM Studio base URL.

## Notes

- LM Studio should expose an OpenAI-compatible server, typically at
  `http://localhost:1234/v1`.
- `uv sync --dev` will install `pytest` for local testing.
