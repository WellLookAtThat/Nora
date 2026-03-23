from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import discord
from yt_dlp import YoutubeDL

LOGGER = logging.getLogger(__name__)

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@dataclass(slots=True)
class Track:
    title: str
    stream_url: str
    webpage_url: str
    requested_by: str
    duration: int | None = None


@dataclass(slots=True)
class GuildMusicState:
    queue: deque[Track] = field(default_factory=deque)
    current: Track | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class MusicManager:
    def __init__(self) -> None:
        self.states: dict[int, GuildMusicState] = {}
        self.ytdl = YoutubeDL(YTDL_OPTIONS)
        self.loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    async def shutdown(self) -> None:
        self.states.clear()

    async def resolve_track(self, query: str, requested_by: str) -> tuple[Track, list[str]]:
        steps: list[str] = []
        providers = [
            query,
            f"ytsearch1:{query}",
            f"scsearch1:{query}",
        ]

        for provider_query in providers:
            try:
                label = "direct" if provider_query == query else provider_query.split(":", 1)[0]
                steps.append(f"Trying source `{label}`...")
                info = await asyncio.to_thread(self.ytdl.extract_info, provider_query, download=False)
                track = self._build_track(info, requested_by)
                steps.append(f"Loaded `{track.title}` successfully.")
                return track, steps
            except Exception as exc:
                LOGGER.warning("Music lookup failed for %s: %s", provider_query, exc)
                steps.append(f"Source `{provider_query}` failed, falling back.")

        raise RuntimeError("I could not find a playable result from the available music providers.")

    def _build_track(self, info: dict[str, Any], requested_by: str) -> Track:
        if "entries" in info:
            entries = [entry for entry in info["entries"] if entry]
            if not entries:
                raise RuntimeError("No results were returned by the provider.")
            info = entries[0]

        stream_url = info.get("url")
        title = info.get("title") or "Unknown title"
        webpage_url = info.get("webpage_url") or info.get("original_url") or ""
        duration = info.get("duration")

        if not stream_url:
            raise RuntimeError("The provider returned a result without a stream URL.")

        return Track(
            title=title,
            stream_url=stream_url,
            webpage_url=webpage_url,
            requested_by=requested_by,
            duration=duration,
        )

    async def enqueue(self, guild_id: int, track: Track) -> GuildMusicState:
        state = self.get_state(guild_id)
        async with state.lock:
            state.queue.append(track)
        return state

    async def skip(self, guild_id: int, voice_client: discord.VoiceClient | None) -> None:
        state = self.get_state(guild_id)
        async with state.lock:
            state.current = None
            if voice_client and voice_client.is_playing():
                voice_client.stop()

    async def stop(self, guild_id: int, voice_client: discord.VoiceClient | None) -> None:
        state = self.get_state(guild_id)
        async with state.lock:
            state.queue.clear()
            state.current = None
            if voice_client:
                voice_client.stop()
                await voice_client.disconnect(force=True)

    async def play_next(
        self,
        guild_id: int,
        voice_client: discord.VoiceClient,
        text_channel: discord.abc.Messageable,
    ) -> None:
        state = self.get_state(guild_id)

        async with state.lock:
            if state.current is not None or not state.queue:
                return

            next_track = state.queue.popleft()
            state.current = next_track

        source = discord.FFmpegPCMAudio(next_track.stream_url, **FFMPEG_OPTIONS)

        def after_playback(error: Exception | None) -> None:
            if error:
                LOGGER.exception("Playback error: %s", error)
            if self.loop is None:
                LOGGER.error("Music event loop has not been bound yet.")
                return
            asyncio.run_coroutine_threadsafe(
                self._after_track(guild_id, voice_client, text_channel, error),
                self.loop,
            )

        voice_client.play(source, after=after_playback)
        await text_channel.send(f"Now playing: **{next_track.title}** requested by **{next_track.requested_by}**")

    async def _after_track(
        self,
        guild_id: int,
        voice_client: discord.VoiceClient,
        text_channel: discord.abc.Messageable,
        error: Exception | None,
    ) -> None:
        state = self.get_state(guild_id)
        async with state.lock:
            state.current = None

        if error:
            await text_channel.send("Playback hit an error, so I'm trying the next queued track if there is one.")

        await self.play_next(guild_id, voice_client, text_channel)
