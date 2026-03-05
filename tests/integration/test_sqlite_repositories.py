from pathlib import Path

import pytest

from video_bot.core.entities import PlatformType, UserRole
from video_bot.infrastructure.database.access_repository import SQLiteAccessRepository
from video_bot.infrastructure.database.bootstrap import initialize_database, sync_superadmins, trim_logs
from video_bot.infrastructure.database.download_log_repository import SQLiteDownloadLogRepository
from video_bot.infrastructure.database.sqlite import SQLiteDatabase


@pytest.mark.asyncio
async def test_sqlite_repositories_store_users_and_logs(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "bot.sqlite3")
    await initialize_database(database)

    access_repository = SQLiteAccessRepository(database)
    log_repository = SQLiteDownloadLogRepository(database)

    await sync_superadmins(access_repository, (1001,))
    await access_repository.upsert_user(telegram_id=1002, role=UserRole.USER)
    users = await access_repository.list_active_users()

    assert [user.telegram_id for user in users] == [1001, 1002]
    assert users[0].role == UserRole.SUPERADMIN

    first = await log_repository.create_log(1001, "https://www.tiktok.com/@creator/video/1", PlatformType.TIKTOK)
    second = await log_repository.create_log(1002, "https://www.instagram.com/reel/ABC/", PlatformType.INSTAGRAM)
    await log_repository.mark_success(first, 1024)
    await log_repository.mark_failure(second, "broken")

    stats = await log_repository.get_stats()
    assert stats.total == 2
    assert stats.success == 1
    assert stats.failed == 1
    assert stats.tiktok == 1
    assert stats.instagram == 1

    recent = await log_repository.get_recent(limit=10)
    assert [item.id for item in recent] == [second, first]


@pytest.mark.asyncio
async def test_trim_logs_keeps_only_last_entries(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "bot.sqlite3")
    await initialize_database(database)
    log_repository = SQLiteDownloadLogRepository(database)

    for index in range(5):
        await log_repository.create_log(index, f"https://example.com/{index}", None)

    await trim_logs(log_repository, 2)
    recent = await log_repository.get_recent(limit=10)

    assert len(recent) == 2
    assert [item.telegram_id for item in recent] == [4, 3]

