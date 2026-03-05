from __future__ import annotations

import asyncio
import logging

from video_bot.config import load_settings
from video_bot.containers import build_container
from video_bot.infrastructure.database.bootstrap import initialize_database, sync_superadmins, trim_logs
from video_bot.presentation.tg_bot import create_bot, create_dispatcher


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    settings = load_settings()
    container = build_container(settings)

    await container.file_storage.ensure_dirs()
    await container.file_storage.cleanup_stale_files()
    await initialize_database(container.database)
    await sync_superadmins(container.access_repository, settings.superadmins)
    await trim_logs(container.download_log_repository, settings.log_retention_limit)

    bot = create_bot(container)
    dispatcher = create_dispatcher(container)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
