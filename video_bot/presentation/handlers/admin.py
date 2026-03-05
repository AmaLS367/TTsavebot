from __future__ import annotations

from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from video_bot.containers import AppContainer
from video_bot.core.entities import User
from video_bot.core.errors import ValidationError
from video_bot.presentation.keyboards.admin_panel import build_admin_panel_keyboard, build_whitelist_keyboard

router = Router(name="admin")


class WhitelistStates(StatesGroup):
    waiting_for_allow_id = State()
    waiting_for_deny_id = State()


@dataclass(slots=True, frozen=True)
class ParsedTelegramID:
    telegram_id: int


def _parse_telegram_id(raw_value: str) -> ParsedTelegramID:
    value = raw_value.strip()
    if not value:
        raise ValidationError("Укажите Telegram ID числом.")
    try:
        return ParsedTelegramID(telegram_id=int(value))
    except ValueError as exc:
        raise ValidationError("Telegram ID должен быть числом.") from exc


def _format_stats(app_stats: object) -> str:
    return (
        "Статистика:\n"
        f"Всего запросов: {app_stats.total}\n"
        f"Успешно: {app_stats.success}\n"
        f"Ошибки: {app_stats.failed}\n"
        f"Отклонено: {app_stats.rejected}\n"
        f"Слишком большие: {app_stats.oversize}\n"
        f"TikTok: {app_stats.tiktok}\n"
        f"Instagram: {app_stats.instagram}"
    )


def _format_logs(logs: list[object]) -> str:
    if not logs:
        return "Логи пока пусты."
    lines = []
    for item in logs:
        lines.append(
            f"#{item.id} | {item.status.value} | user={item.telegram_id} | "
            f"{item.platform.value if item.platform else 'n/a'} | {item.url}"
        )
    return "\n".join(lines)


@router.message(Command("panel"))
async def panel_handler(message: Message) -> None:
    await message.answer("Админ-панель", reply_markup=build_admin_panel_keyboard())


@router.message(Command("stats"))
async def stats_handler(message: Message, app_container: AppContainer) -> None:
    stats = await app_container.admin_get_stats_use_case.execute()
    await message.answer(_format_stats(stats))


@router.message(Command("logs"))
async def logs_handler(message: Message, app_container: AppContainer) -> None:
    logs = await app_container.admin_get_logs_use_case.execute(limit=10)
    await message.answer(_format_logs(logs))


@router.message(Command("allow"))
async def allow_handler(message: Message, app_container: AppContainer) -> None:
    try:
        raw_args = message.text.partition(" ")[2]
        target = _parse_telegram_id(raw_args)
        user = await app_container.admin_allow_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {user.telegram_id} добавлен в whitelist.")
    except ValidationError as exc:
        await message.answer(str(exc))


@router.message(Command("deny"))
async def deny_handler(message: Message, app_container: AppContainer) -> None:
    try:
        raw_args = message.text.partition(" ")[2]
        target = _parse_telegram_id(raw_args)
        await app_container.admin_deny_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} удалён из whitelist.")
    except ValidationError as exc:
        await message.answer(str(exc))


@router.callback_query(F.data == "panel:stats")
async def panel_stats_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    stats = await app_container.admin_get_stats_use_case.execute()
    await callback.message.edit_text(_format_stats(stats), reply_markup=build_admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "panel:logs")
async def panel_logs_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    logs = await app_container.admin_get_logs_use_case.execute(limit=10)
    await callback.message.edit_text(_format_logs(logs), reply_markup=build_admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "panel:whitelist")
async def panel_whitelist_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Управление whitelist", reply_markup=build_whitelist_keyboard())
    await callback.answer()


@router.callback_query(F.data == "panel:back")
async def panel_back_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Админ-панель", reply_markup=build_admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "panel:allow")
async def panel_allow_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WhitelistStates.waiting_for_allow_id)
    await callback.message.answer("Отправьте Telegram ID, который нужно добавить в whitelist.")
    await callback.answer()


@router.callback_query(F.data == "panel:deny")
async def panel_deny_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WhitelistStates.waiting_for_deny_id)
    await callback.message.answer("Отправьте Telegram ID, который нужно удалить из whitelist.")
    await callback.answer()


@router.callback_query(F.data == "panel:users")
async def panel_users_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    users = await app_container.access_repository.list_active_users()
    if not users:
        text = "Whitelist пуст."
    else:
        text = "\n".join(f"{user.telegram_id} | {user.role.value}" for user in users)
    await callback.message.answer(text)
    await callback.answer()


@router.message(WhitelistStates.waiting_for_allow_id)
async def process_allow_id(message: Message, state: FSMContext, app_container: AppContainer) -> None:
    try:
        target = _parse_telegram_id(message.text or "")
        await app_container.admin_allow_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} добавлен в whitelist.")
        await state.clear()
    except ValidationError as exc:
        await message.answer(str(exc))


@router.message(WhitelistStates.waiting_for_deny_id)
async def process_deny_id(message: Message, state: FSMContext, app_container: AppContainer) -> None:
    try:
        target = _parse_telegram_id(message.text or "")
        await app_container.admin_deny_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} удалён из whitelist.")
        await state.clear()
    except ValidationError as exc:
        await message.answer(str(exc))
