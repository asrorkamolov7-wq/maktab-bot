"""Maslahatchiga murojaat."""
from __future__ import annotations

import logging
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..config import Settings
from ..database import Database
from ..keyboards import main_keyboard
from ..states import SupportState
from ..utils import esc, user_link

logger = logging.getLogger(__name__)

router = Router(name="support")
router.message.filter(F.chat.type == "private")

THROTTLE_SECONDS = 15
_last_sent: dict[int, float] = {}


@router.message(SupportState.waiting_message)
async def process_inquiry(message: Message, state: FSMContext, bot: Bot, db: Database, settings: Settings) -> None:
    user = message.from_user
    now = time.monotonic()
    if now - _last_sent.get(user.id, 0.0) < THROTTLE_SECONDS:
        await message.answer("⏳ Iltimos, keyingi murojaatni yuborishdan oldin biroz kuting.")
        return

    username = f" @{esc(user.username)}" if user.username else ""
    header = (
        "📬 <b>Yangi murojaat</b>\n"
        f"👤 {user_link(user)}{username}\n"
        f"🆔 <code>{user.id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Javob berish uchun shu xabarga (yoki quyidagi nusxasiga) Reply qiling.</i>"
    )

    delivered = 0
    for admin_id in settings.admin_ids:
        try:
            head = await bot.send_message(admin_id, header)
            copy = await message.copy_to(admin_id)
            await db.link_feedback(admin_id, head.message_id, user.id, user.full_name)
            await db.link_feedback(admin_id, copy.message_id, user.id, user.full_name)
            delivered += 1
        except TelegramAPIError:
            logger.warning("Murojaatni adminga (%s) yetkazib bo'lmadi", admin_id, exc_info=True)

    if not delivered:
        await message.answer("Xabarni yuborishda xatolik yuz berdi. Keyinroq urinib ko'ring.")
        return

    _last_sent[user.id] = now
    await state.clear()
    await message.answer(
        "✅ <b>Xabaringiz maktab maslahatchisiga yetkazildi!</b>\nTez orada bot orqali sizga javob qaytariladi.",
        reply_markup=main_keyboard(user.id in settings.admin_ids),
    )
