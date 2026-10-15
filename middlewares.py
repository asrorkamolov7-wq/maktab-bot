from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from .database import Database

logger = logging.getLogger(__name__)


class TrackUserMiddleware(BaseMiddleware):
    """Har bir shaxsiy muloqotdagi foydalanuvchini bazada yangilab turadi.

    Baza tozalansa ham foydalanuvchilar e'lon ro'yxatiga qayta tushadi,
    botni blokdan chiqargan foydalanuvchi esa avtomatik tiklanadi.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        if user and not user.is_bot and (chat is None or chat.type == "private"):
            try:
                await self.db.upsert_user(user.id, user.full_name, user.username)
            except Exception:  # noqa: BLE001 — kuzatuv xatosi asosiy ishni to'xtatmasin
                logger.exception("Foydalanuvchini yangilashda xatolik")
        return await handler(event, data)
