# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram-to-Max crossposting bot. Automatically forwards messages (text and photos with captions) from a Telegram channel to a Max messenger chat using an event-driven async architecture. Requires Python 3.10+ (uses `str | None` union syntax).

## Setup and Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Architecture

Single-file Python app (`bot.py`) using `python-telegram-bot` for receiving Telegram channel posts and `httpx` for async HTTP calls to the Max Bot API.

**Flow:** Telegram channel post → `handle_channel_post()` routes by content type → text goes to `send_max_text()`, photos go through `upload_max_photo()` → `send_max_photo()`.

**Configuration:** Environment variables only (`TELEGRAM_BOT_TOKEN`, `MAX_BOT_TOKEN`, `MAX_CHAT_ID`), loaded via `python-dotenv`. See `.env.example` for template.
