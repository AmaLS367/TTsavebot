from __future__ import annotations

from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from video_bot.containers import AppContainer
from video_bot.core.entities import User
from video_bot.core.errors import DownloadTimeoutError, DownloaderError, FileTooLargeError, PrivateContentError, ValidationError

router = Router(name="downloads")


def _map_error(error: Exception) -> str:
    if isinstance(error, FileTooLargeError):
        return "Файл слишком большой для отправки через Telegram."
    if isinstance(error, PrivateContentError):
        return "Видео недоступно: аккаунт приватный или требуется авторизация."
    if isinstance(error, DownloadTimeoutError):
        return "Скачивание заняло слишком много времени и было остановлено."
    if isinstance(error, ValidationError):
        return str(error)
    if isinstance(error, DownloaderError):
        return "Не удалось скачать видео. Проверьте ссылку или попробуйте позже."
    return "Произошла непредвиденная ошибка при скачивании."


@router.message(F.text.regexp(r"https?://"))
async def download_handler(message: Message, current_user: User, app_container: AppContainer) -> None:
    text = (message.text or "").strip()
    user_lock = app_container.get_user_lock(current_user.telegram_id)
    if user_lock.locked():
        await message.answer("У вас уже выполняется скачивание. Дождитесь завершения текущей загрузки.")
        return

    progress_message = await message.answer("⏳ Загрузка видео, пожалуйста подождите...")

    async with user_lock:
        file_path = None
        try:
            _, video = await app_container.download_video_use_case.execute(url=text, telegram_id=current_user.telegram_id)
            file_path = video.file_path
            await message.answer_video(
                video=FSInputFile(video.file_path),
                caption=video.title or "Видео готово.",
            )
            await progress_message.delete()
        except Exception as exc:
            await progress_message.edit_text(_map_error(exc))
        finally:
            if file_path is not None:
                await app_container.file_storage.remove_file(file_path)

