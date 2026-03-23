from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psutil


@dataclass(slots=True)
class Snapshot:
    uptime_seconds: int
    cpu_percent: float
    memory_mb: int
    gateway_latency_ms: int
    guild_count: int
    user_count: int


class StatusSnapshot:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.process = psutil.Process()

    def build(self) -> Snapshot:
        now = datetime.now(timezone.utc)
        uptime_seconds = int((now - self.bot.started_at).total_seconds())
        memory_mb = int(self.process.memory_info().rss / (1024 * 1024))
        cpu_percent = psutil.cpu_percent(interval=None)
        gateway_latency_ms = round(self.bot.latency * 1000)
        user_count = sum(guild.member_count or 0 for guild in self.bot.guilds)

        return Snapshot(
            uptime_seconds=uptime_seconds,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            gateway_latency_ms=gateway_latency_ms,
            guild_count=len(self.bot.guilds),
            user_count=user_count,
        )
