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

## Installing (macOS)

Run the one-line installer — it downloads the latest release, installs to `/Applications`, and removes the Gatekeeper quarantine flag:

```bash
curl -fsSL https://raw.githubusercontent.com/michaelabrowne/chatMate/develop/install.sh | bash
```

Then create your config directory:

```bash
mkdir -p ~/.config/chatmate
```

Copy `config.yaml` from this repo (or write your own) to `~/.config/chatmate/config.yaml`, then create `~/.config/chatmate/.env` with your API keys:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LMSTUDIO_API_KEY=lm-studio
```

The installed app always checks `~/.config/chatmate/config.yaml` first, so changes there survive app updates.

> **macOS Local Network permission** — on first launch macOS may ask if ChatMate can access the local network. Click Allow, otherwise connections to LM Studio (or any local endpoint) will silently time out.

## Quick Start (from source)

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
4. Set `provider.lmstudio.base_url` to `http://localhost:1234/v1` for a local server, or the machine's LAN IP (e.g. `http://192.168.50.102:1234/v1`) if LM Studio runs on another machine.
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

- Chats are auto-saved under `~/.chatmate/chats`
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
