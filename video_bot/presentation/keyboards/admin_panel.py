from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика", callback_data="panel:stats")
    builder.button(text="Последние логи", callback_data="panel:logs")
    builder.button(text="Whitelist", callback_data="panel:whitelist")
    builder.adjust(1)
    return builder.as_markup()


def build_whitelist_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить ID", callback_data="panel:allow")
    builder.button(text="Удалить ID", callback_data="panel:deny")
    builder.button(text="Список пользователей", callback_data="panel:users")
    builder.button(text="Назад", callback_data="panel:back")
    builder.adjust(1)
    return builder.as_markup()

