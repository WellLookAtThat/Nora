from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def ensure_voice(
        self, interaction: discord.Interaction
    ) -> tuple[discord.VoiceClient | None, discord.VoiceChannel | None]:
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member) or user.voice is None or user.voice.channel is None:
            return None, None

        voice_channel = user.voice.channel
        voice_client = guild.voice_client

        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        return voice_client, voice_channel

    @app_commands.command(name="play", description="Queue and play music from a search query or URL.")
    @app_commands.describe(query="A song title, playlist item, or direct URL")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)

        voice_client, voice_channel = await self.ensure_voice(interaction)
        if voice_client is None or voice_channel is None or interaction.guild is None:
            await interaction.followup.send("Join a voice channel first so I know where to play music.")
            return

        await interaction.followup.send(f"Looking for `{query}` and preparing a playable source. I’ll report each fallback step here.")

        try:
            track, steps = await self.bot.music.resolve_track(query, interaction.user.display_name)
        except Exception as exc:
            await interaction.followup.send(f"I couldn’t load that track: `{exc}`")
            return

        for step in steps:
            await interaction.followup.send(step)

        state = await self.bot.music.enqueue(interaction.guild.id, track)
        await interaction.followup.send(
            f"Queued **{track.title}** in **{voice_channel.name}**. Queue length is now **{len(state.queue)}**."
        )

        if not voice_client.is_playing() and state.current is None:
            await self.bot.music.play_next(interaction.guild.id, voice_client, interaction.channel)

    @app_commands.command(name="skip", description="Skip the current track.")
    async def skip(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await self.bot.music.skip(guild.id, guild.voice_client)
        await interaction.response.send_message("Skipped the current track. I’m moving on if anything else is queued.")
        if guild.voice_client:
            await self.bot.music.play_next(guild.id, guild.voice_client, interaction.channel)

    @app_commands.command(name="stop", description="Stop playback, clear the queue, and disconnect.")
    async def stop(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await self.bot.music.stop(guild.id, guild.voice_client)
        await interaction.response.send_message("Stopped playback, cleared the queue, and disconnected from voice.")

    @app_commands.command(name="queue", description="Show the current music queue.")
    async def queue(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        state = self.bot.music.get_state(guild.id)
        current = state.current.title if state.current else "Nothing playing"
        upcoming = "\n".join(f"{index}. {track.title}" for index, track in enumerate(state.queue, start=1)) or "Queue is empty"

        embed = discord.Embed(title="Music Queue", color=discord.Color.orange())
        embed.add_field(name="Current", value=current, inline=False)
        embed.add_field(name="Upcoming", value=upcoming[:1024], inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))
