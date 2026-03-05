from __future__ import annotations

import asyncio
from dataclasses import dataclass

from video_bot.config import Settings
from video_bot.core.interfaces import IAccessRepository, IDownloadLogRepository, IFileStorage, IVideoDownloaderService
from video_bot.core.use_cases import (
    AdminAllowUserUseCase,
    AdminDenyUserUseCase,
    AdminGetLogsUseCase,
    AdminGetStatsUseCase,
    CheckAccessUseCase,
    DownloadVideoUseCase,
)
from video_bot.infrastructure.database.access_repository import SQLiteAccessRepository
from video_bot.infrastructure.database.download_log_repository import SQLiteDownloadLogRepository
from video_bot.infrastructure.database.sqlite import SQLiteDatabase
from video_bot.infrastructure.downloaders.ytdlp_downloader import YtDlpDownloader
from video_bot.infrastructure.storage.local_file_storage import LocalFileStorage


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    database: SQLiteDatabase
    access_repository: IAccessRepository
    download_log_repository: IDownloadLogRepository
    file_storage: IFileStorage
    downloader: IVideoDownloaderService
    check_access_use_case: CheckAccessUseCase
    download_video_use_case: DownloadVideoUseCase
    admin_allow_user_use_case: AdminAllowUserUseCase
    admin_deny_user_use_case: AdminDenyUserUseCase
    admin_get_stats_use_case: AdminGetStatsUseCase
    admin_get_logs_use_case: AdminGetLogsUseCase
    user_locks: dict[int, asyncio.Lock]

    def get_user_lock(self, telegram_id: int) -> asyncio.Lock:
        lock = self.user_locks.get(telegram_id)
        if lock is None:
            lock = asyncio.Lock()
            self.user_locks[telegram_id] = lock
        return lock


def build_container(settings: Settings) -> AppContainer:
    database = SQLiteDatabase(settings.db_path)
    access_repository = SQLiteAccessRepository(database)
    download_log_repository = SQLiteDownloadLogRepository(database)
    file_storage = LocalFileStorage(settings.downloads_dir, settings.stale_file_max_age_hours)
    downloader = YtDlpDownloader(
        ytdlp_bin=settings.ytdlp_bin,
        downloads_dir=settings.downloads_dir,
        timeout_seconds=settings.ytdlp_timeout_seconds,
        cookies_path=settings.instagram_cookies_path,
    )

    return AppContainer(
        settings=settings,
        database=database,
        access_repository=access_repository,
        download_log_repository=download_log_repository,
        file_storage=file_storage,
        downloader=downloader,
        check_access_use_case=CheckAccessUseCase(access_repository),
        download_video_use_case=DownloadVideoUseCase(
            downloader=downloader,
            file_storage=file_storage,
            log_repository=download_log_repository,
            max_file_size_bytes=settings.max_file_size_bytes,
            log_retention_limit=settings.log_retention_limit,
        ),
        admin_allow_user_use_case=AdminAllowUserUseCase(access_repository),
        admin_deny_user_use_case=AdminDenyUserUseCase(access_repository),
        admin_get_stats_use_case=AdminGetStatsUseCase(download_log_repository),
        admin_get_logs_use_case=AdminGetLogsUseCase(download_log_repository),
        user_locks={},
    )

