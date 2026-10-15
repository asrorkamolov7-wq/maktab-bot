from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent

from .config import load_settings
from .database import Database
from .handlers import admin, fallback, menu, support, survey
from .middlewares import TrackUserMiddleware
from .web import start_web_server

logger = logging.getLogger(__name__)

USER_COMMANDS = [
    BotCommand(command="start", description="Asosiy menyu"),
    BotCommand(command="cancel", description="Jarayonni bekor qilish"),
]
ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="stats", description="Statistika"),
    BotCommand(command="surveys", description="So'rovnomalarni boshqarish"),
    BotCommand(command="add_survey", description="Yangi so'rovnoma qo'shish"),
    BotCommand(command="export", description="Excel hisobot"),
    BotCommand(command="post", description="Hammaga e'lon yuborish"),
    BotCommand(command="sms", description="Foydalanuvchiga xabar"),
]


async def on_error(event: ErrorEvent, bot: Bot) -> bool:
    logger.exception("Ishlov berilmagan xatolik: %s", event.exception, exc_info=event.exception)
    update = event.update
    chat_id = None
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.from_user.id
        try:
            await update.callback_query.answer()
        except Exception:  # noqa: BLE001
            pass
    if chat_id:
        try:
            await bot.send_message(chat_id, "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, /start ni bosib qayta urinib ko'ring.")
        except Exception:  # noqa: BLE001
            pass
    return True


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    settings = load_settings()
    db = await Database.connect(settings.db_path)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(
        storage=MemoryStorage(),
        events_isolation=SimpleEventIsolation(),  # bir foydalanuvchining hodisalari ketma-ket ishlanadi
        db=db,
        settings=settings,
    )

    tracker = TrackUserMiddleware(db)
    dp.message.outer_middleware(tracker)
    dp.callback_query.outer_middleware(tracker)

    # Tartib muhim: menyu -> admin -> holat handlerlari -> fallback
    dp.include_routers(menu.router, admin.router, survey.router, support.router, fallback.router)
    dp.errors.register(on_error)

    runner = await start_web_server(settings.port)
    try:
        await bot.set_my_commands(USER_COMMANDS)
        for admin_id in settings.admin_ids:
            try:
                await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))
            except Exception:  # noqa: BLE001 — admin hali botni ishga tushirmagan bo'lishi mumkin
                logger.warning("Admin (%s) uchun buyruqlar o'rnatilmadi", admin_id)

        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Bot ishga tushdi.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await runner.cleanup()
        await bot.session.close()
        await db.close()


def run() -> None:
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
