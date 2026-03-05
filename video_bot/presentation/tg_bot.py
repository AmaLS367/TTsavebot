from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from video_bot.containers import AppContainer
from video_bot.presentation.handlers import admin, common, downloads
from video_bot.presentation.middlewares.auth import AuthMiddleware
from video_bot.presentation.middlewares.superadmin import SuperadminMiddleware


def create_bot(container: AppContainer) -> Bot:
    return Bot(
        token=container.settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(container: AppContainer) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher["app_container"] = container
    auth_middleware = AuthMiddleware(container)

    common.router.message.middleware(auth_middleware)
    downloads.router.message.middleware(auth_middleware)
    admin.router.message.middleware(auth_middleware)
    admin.router.callback_query.middleware(auth_middleware)

    superadmin_middleware = SuperadminMiddleware()
    admin.router.message.middleware(superadmin_middleware)
    admin.router.callback_query.middleware(superadmin_middleware)

    dispatcher.include_router(admin.router)
    dispatcher.include_router(downloads.router)
    dispatcher.include_router(common.router)
    return dispatcher

