from dataclasses import dataclass, field
from pathlib import Path

import pytest

from video_bot.core.entities import DownloadedVideo, PlatformType
from video_bot.core.errors import DownloadTimeoutError, FileTooLargeError
from video_bot.core.interfaces import DownloadLogRecord, DownloadStats, IDownloadLogRepository, IFileStorage, IVideoDownloaderService
from video_bot.core.use_cases import DownloadVideoUseCase


@dataclass
class FakeDownloader(IVideoDownloaderService):
    result: DownloadedVideo | None = None
    error: Exception | None = None

    async def download(self, url: str) -> DownloadedVideo:
        if self.error:
            raise self.error
        if self.result is None:
            raise RuntimeError("No result configured")
        return self.result


@dataclass
class FakeFileStorage(IFileStorage):
    sizes: dict[Path, int]
    removed: list[Path] = field(default_factory=list)

    async def ensure_dirs(self) -> None:
        return None

    async def remove_file(self, path: Path) -> None:
        self.removed.append(path)

    async def cleanup_stale_files(self) -> int:
        return 0

    async def file_size(self, path: Path) -> int:
        return self.sizes[path]


@dataclass
class FakeLogRepository(IDownloadLogRepository):
    created_logs: list[tuple[int, str, PlatformType | None]] = field(default_factory=list)
    success: list[tuple[int, int]] = field(default_factory=list)
    failed: list[tuple[int, str]] = field(default_factory=list)
    rejected: list[tuple[int, str]] = field(default_factory=list)
    oversize: list[tuple[int, int, str]] = field(default_factory=list)
    trimmed: list[int] = field(default_factory=list)

    async def create_log(self, telegram_id: int, url: str, platform: PlatformType | None) -> int:
        self.created_logs.append((telegram_id, url, platform))
        return len(self.created_logs)

    async def mark_success(self, log_id: int, file_size_bytes: int) -> None:
        self.success.append((log_id, file_size_bytes))

    async def mark_failure(self, log_id: int, error_message: str) -> None:
        self.failed.append((log_id, error_message))

    async def mark_rejected(self, log_id: int, error_message: str) -> None:
        self.rejected.append((log_id, error_message))

    async def mark_oversize(self, log_id: int, file_size_bytes: int, error_message: str) -> None:
        self.oversize.append((log_id, file_size_bytes, error_message))

    async def get_recent(self, limit: int) -> list[DownloadLogRecord]:
        return []

    async def get_stats(self) -> DownloadStats:
        return DownloadStats(total=0, success=0, failed=0, rejected=0, oversize=0, tiktok=0, instagram=0)

    async def trim_to_limit(self, limit: int) -> None:
        self.trimmed.append(limit)


def _video(path: Path) -> DownloadedVideo:
    return DownloadedVideo(
        source_url="https://www.tiktok.com/@creator/video/123",
        platform=PlatformType.TIKTOK,
        file_path=path,
        file_size_bytes=123,
        title="clip",
        extractor_id="123",
    )


@pytest.mark.asyncio
async def test_download_video_use_case_happy_path(tmp_path: Path) -> None:
    path = tmp_path / "video.mp4"
    log_repository = FakeLogRepository()
    file_storage = FakeFileStorage({path: 1024})
    use_case = DownloadVideoUseCase(
        downloader=FakeDownloader(result=_video(path)),
        file_storage=file_storage,
        log_repository=log_repository,
        max_file_size_bytes=10_000,
        log_retention_limit=50,
    )

    _, result = await use_case.execute("https://www.tiktok.com/@creator/video/123", telegram_id=1)

    assert result.file_path == path
    assert log_repository.success == [(1, 1024)]
    assert log_repository.trimmed == [50]


@pytest.mark.asyncio
async def test_download_video_use_case_marks_oversize_and_removes_file(tmp_path: Path) -> None:
    path = tmp_path / "large.mp4"
    log_repository = FakeLogRepository()
    file_storage = FakeFileStorage({path: 20_000})
    use_case = DownloadVideoUseCase(
        downloader=FakeDownloader(result=_video(path)),
        file_storage=file_storage,
        log_repository=log_repository,
        max_file_size_bytes=1_000,
        log_retention_limit=50,
    )

    with pytest.raises(FileTooLargeError):
        await use_case.execute("https://www.tiktok.com/@creator/video/123", telegram_id=1)

    assert log_repository.oversize
    assert file_storage.removed == [path]
    assert log_repository.failed == []


@pytest.mark.asyncio
async def test_download_video_use_case_marks_failure_on_downloader_error() -> None:
    log_repository = FakeLogRepository()
    file_storage = FakeFileStorage({})
    use_case = DownloadVideoUseCase(
        downloader=FakeDownloader(error=DownloadTimeoutError("timeout")),
        file_storage=file_storage,
        log_repository=log_repository,
        max_file_size_bytes=1_000,
        log_retention_limit=50,
    )

    with pytest.raises(DownloadTimeoutError):
        await use_case.execute("https://www.tiktok.com/@creator/video/123", telegram_id=1)

    assert log_repository.failed == [(1, "timeout")]
    assert log_repository.trimmed == [50]
