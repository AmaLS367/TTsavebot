from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from video_bot.core.entities import User

router = Router(name="common")


@router.message(Command("start"))
async def start_handler(message: Message, current_user: User) -> None:
    await message.answer(
        "Привет. Пришлите ссылку на TikTok или Instagram Reel/Post, и я попробую скачать видео.\n"
        f"Ваш ID: `{current_user.telegram_id}`",
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def help_handler(message: Message, current_user: User) -> None:
    commands = [
        "/start - приветствие",
        "/help - справка",
        "/whoami - показать текущую роль",
    ]
    if current_user.is_superadmin:
        commands.extend(
            [
                "/panel - открыть админ-панель",
                "/allow <id> - разрешить доступ",
                "/deny <id> - запретить доступ",
                "/stats - статистика скачиваний",
                "/logs - последние логи",
            ]
        )

    await message.answer("Доступные команды:\n" + "\n".join(commands))


@router.message(Command("whoami"))
async def whoami_handler(message: Message, current_user: User) -> None:
    await message.answer(f"Ваш ID: {current_user.telegram_id}\nРоль: {current_user.role.value}")


@router.message(F.text)
async def fallback_text_handler(message: Message) -> None:
    await message.answer("Отправьте ссылку на TikTok или Instagram Reel/Post.")

