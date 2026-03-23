from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

from bot.config import Settings
from bot.services.music import MusicManager
from bot.services.status import StatusSnapshot

LOGGER = logging.getLogger(__name__)


class AdvancedDiscordBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True

        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None,
        )

        self.settings = settings
        self.started_at = datetime.now(timezone.utc)
        self.music = MusicManager()
        self.status_service = StatusSnapshot(self)

    async def setup_hook(self) -> None:
        for extension in (
            "bot.cogs.general",
            "bot.cogs.status",
            "bot.cogs.music",
        ):
            await self.load_extension(extension)

        self.rotate_presence.start()
        synced = await self.tree.sync()
        LOGGER.info("Synced %s app commands", len(synced))

    async def on_ready(self) -> None:
        self.music.bind_loop(asyncio.get_running_loop())
        LOGGER.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        LOGGER.exception("Command error: %s", error)
        await ctx.reply(f"I hit an error while processing that command: `{error}`")

    async def close(self) -> None:
        self.rotate_presence.cancel()
        await self.music.shutdown()
        await super().close()

    @tasks.loop(seconds=45)
    async def rotate_presence(self) -> None:
        snapshot = self.status_service.build()
        activities = [
            f"Nora is active in {len(self.guilds)} servers",
            f"{snapshot.gateway_latency_ms}ms gateway latency",
            f"{snapshot.memory_mb}MB RAM in use",
            "watching over queues and fallbacks",
        ]

        message = activities[int(asyncio.get_running_loop().time()) % len(activities)]
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=message))

    @rotate_presence.before_loop
    async def before_rotate_presence(self) -> None:
        self.rotate_presence.change_interval(seconds=self.settings.status_rotation_seconds)
        await self.wait_until_ready()
