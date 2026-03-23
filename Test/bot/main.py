from __future__ import annotations

import logging

from bot.config import load_settings
from bot.core.bot import AdvancedDiscordBot
from bot.logging_config import configure_logging


def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Nora")

    bot = AdvancedDiscordBot(settings)
    bot.run(settings.token, log_handler=None)
