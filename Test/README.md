# Nora

Nora is a Python-first foundation for a large Discord bot with:

- Slash commands and prefix commands
- Music playback with queueing and fallback search providers
- Chat-visible progress updates so users can see what the bot is doing
- Detailed status commands for bot health and Discord server information
- A modular cog and service architecture for adding moderation, economy, AI, games, tickets, and more

## What is included now

- A production-friendly bot entrypoint
- Environment-based configuration
- Structured logging
- Music service with queue management and fallback extraction flow
- `/play`, `/skip`, `/stop`, `/queue`
- `/serverstatus`, `/botstatus`, `/ping`

## Important reality check

No bot can literally have "every single capability" in one pass, and some features of large public bots depend on:

- External APIs
- Persistent databases
- FFmpeg installed on the host
- Permission-sensitive moderation features
- Separate music, analytics, and automation services

This scaffold is designed so we can grow toward that cleanly.

## Setup

1. Install Python 3.11 or newer.
2. Install FFmpeg and make sure `ffmpeg` is in your system PATH.
3. Copy `.env.example` to `.env` and fill in your Discord bot token.
4. Install dependencies:

```bash
pip install -e .
```

5. Start the bot:

```bash
python -m bot
```

## Recommended next features

- Moderation system with warns, mutes, automod, and logs
- Database-backed settings and per-guild configuration
- Ticketing and support panels
- Reaction roles
- Starboard
- Custom reminders and scheduled jobs
- AI chat tools with safety controls
- Web dashboard
- Lavalink or dedicated audio backend for larger music workloads

## Commands

- `/ping`
- `/botstatus`
- `/serverstatus`
- `/play query:<song name or url>`
- `/skip`
- `/stop`
- `/queue`

## Notes on "tick rate"

Discord guilds do not expose a true server tick rate value the way a game server does. This bot reports practical real-time health metrics instead:

- Gateway latency
- Uptime
- CPU and memory use
- Voice connection state
- Guild statistics

If you want actual game server tick rate, we can add dedicated integrations for Minecraft, FiveM, Source, Rust, or other servers later.
