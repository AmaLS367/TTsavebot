from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from video_bot.containers import AppContainer


class AuthMiddleware(BaseMiddleware):
    def __init__(self, container: AppContainer) -> None:
        self._container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = getattr(getattr(event, "from_user", None), "id", None)
        if telegram_id is None:
            return await handler(event, data)

        user = await self._container.check_access_use_case.execute(telegram_id)
        if user is None:
            await self._log_rejection(telegram_id, event)
            await self._deny(event)
            return None

        data["current_user"] = user
        return await handler(event, data)

    async def _log_rejection(self, telegram_id: int, event: TelegramObject) -> None:
        payload = ""
        platform = None
        if isinstance(event, Message):
            payload = event.text or event.caption or "<empty>"
            try:
                platform = None
            except Exception:
                platform = None
        elif isinstance(event, CallbackQuery):
            payload = f"callback:{event.data}"

        log_id = await self._container.download_log_repository.create_log(
            telegram_id=telegram_id,
            url=payload,
            platform=platform,
        )
        await self._container.download_log_repository.mark_rejected(log_id, "Пользователь не в whitelist.")
        await self._container.download_log_repository.trim_to_limit(self._container.settings.log_retention_limit)

    @staticmethod
    async def _deny(event: TelegramObject) -> None:
        if isinstance(event, Message):
            await event.answer("Доступ запрещён.")
        elif isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещён.", show_alert=True)

