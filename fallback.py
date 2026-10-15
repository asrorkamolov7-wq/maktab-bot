"""Boshqa hech bir handler ushlamagan hodisalar."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from keyboards import main_keyboard

router = Router(name="fallback")


@router.message(F.chat.type == "private", StateFilter(None))
async def unknown_message(message: Message, settings: Settings) -> None:
    await message.answer(
        "Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_keyboard(message.from_user.id in settings.admin_ids),
    )


@router.callback_query()
async def stale_callback(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan. /start buyrug'ini bosing.", show_alert=True)
