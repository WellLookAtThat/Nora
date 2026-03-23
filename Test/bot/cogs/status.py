from __future__ import annotations

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


class StatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="botstatus", description="Show detailed runtime health for the bot.")
    async def botstatus(self, interaction: discord.Interaction) -> None:
        snapshot = self.bot.status_service.build()
        uptime = str(timedelta(seconds=snapshot.uptime_seconds))

        embed = discord.Embed(title="Bot Status", color=discord.Color.blurple())
        embed.add_field(name="Gateway Latency", value=f"{snapshot.gateway_latency_ms}ms", inline=True)
        embed.add_field(name="CPU Use", value=f"{snapshot.cpu_percent:.1f}%", inline=True)
        embed.add_field(name="Memory Use", value=f"{snapshot.memory_mb} MB", inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Guilds", value=str(snapshot.guild_count), inline=True)
        embed.add_field(name="Users", value=str(snapshot.user_count), inline=True)
        embed.set_footer(text="Discord does not expose a true guild tick rate, so latency and runtime metrics are shown instead.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverstatus", description="Show detailed information about this Discord server.")
    async def serverstatus(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        embed = discord.Embed(title=f"{guild.name} Status", color=discord.Color.green())
        embed.add_field(name="Members", value=str(guild.member_count or 0), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Boost Tier", value=str(guild.premium_tier), inline=True)
        embed.add_field(name="Boost Count", value=str(guild.premium_subscription_count or 0), inline=True)
        embed.add_field(name="Emoji Count", value=str(len(guild.emojis)), inline=True)
        embed.add_field(name="Bot Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Shard ID", value=str(guild.shard_id or 0), inline=True)
        embed.add_field(name="Verification", value=str(guild.verification_level), inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatusCog(bot))
