"""Admin paneli: so'rovnomalar, statistika, hisobot, e'lon, shaxsiy xabar, murojaatga javob."""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.exceptions import (
    SkipHandler,
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import Settings
from database import Database
from excel_report import UZ_TZ, build_report
from filters import IsAdmin
from keyboards import (
    Btn,
    broadcast_confirm_keyboard,
    cancel_keyboard,
    delete_confirm_keyboard,
    main_keyboard,
    surveys_admin_keyboard,
)
from states import AdminState
from survey_parser import parse_survey_text
from texts import SURVEY_TEMPLATE
from utils import esc, grade_key

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(IsAdmin())

_background_tasks: set[asyncio.Task] = set()
_COMMAND_PREFIX = re.compile(r"^/\w+(@\w+)?\s*")


def _strip_command(text: str | None) -> str:
    return _COMMAND_PREFIX.sub("", text or "", count=1).strip()


async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "not modified" not in str(e).lower():
            raise


# =====================================================================
# 1) Yangi so'rovnoma qo'shish
# =====================================================================
@router.message(F.text == Btn.ADD_SURVEY)
@router.message(Command("add_survey"))
async def add_survey_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📝 <b>Yangi so'rovnomani bitta xabar shaklida yuboring.</b>\n\n"
        "<b>Namuna:</b>\n"
        f"<pre>{esc(SURVEY_TEMPLATE)}</pre>\n"
        "<i>Qoidalar:</i>\n"
        "• <i>Sinflar: 9-11 yoki 5, 6, 9 ko'rinishida (5–11).</i>\n"
        "• <i>Savoldan keyin «-» bilan variantlar yozilsa — tanlovli savol (kamida 2 ta).</i>\n"
        "• <i>Variant yozilmasa yoki [yozma] bo'lsa — o'quvchi o'zi yozadi.</i>\n\n"
        "Bekor qilish uchun pastdagi tugmani bosing.",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(AdminState.waiting_survey_text)


# =====================================================================
# 2) So'rovnomalar ro'yxati (yoqish/o'chirish)
# =====================================================================
async def _render_survey_list(db: Database):
    surveys = await db.list_surveys()
    if not surveys:
        return "So'rovnomalar hali yo'q. «➕ Yangi so'rovnoma qo'shish» tugmasidan foydalaning.", None
    items = [(s, await db.count_submissions(s.id)) for s in surveys]
    lines = ["📋 <b>So'rovnomalar</b>", "🟢 faol • 🔴 to'xtatilgan\n"]
    for n, (s, count) in enumerate(items, start=1):
        mark = "🟢" if s.is_active else "🔴"
        grades = ", ".join(map(str, s.grades))
        lines.append(
            f"<b>{n}.</b> {mark} {esc(s.title)}\n"
            f"    Sinflar: {grades} • Savollar: {len(s.questions)} • Javoblar: {count}"
        )
    return "\n".join(lines), surveys_admin_keyboard(items)


@router.message(F.text == Btn.SURVEYS)
@router.message(Command("surveys"))
async def surveys_list(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    text, kb = await _render_survey_list(db)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "adm_list")
async def cb_list(cb: CallbackQuery, db: Database) -> None:
    text, kb = await _render_survey_list(db)
    await _safe_edit(cb.message, text, kb)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_tg:"))
async def cb_toggle(cb: CallbackQuery, db: Database) -> None:
    survey = await db.get_survey(cb.data.split(":", 1)[1])
    if survey is None:
        await cb.answer("So'rovnoma topilmadi.", show_alert=True)
        return
    await db.set_survey_active(survey.id, not survey.is_active)
    await cb.answer("🟢 Yoqildi" if not survey.is_active else "🔴 To'xtatildi")
    text, kb = await _render_survey_list(db)
    await _safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("adm_del:"))
async def cb_delete_ask(cb: CallbackQuery, db: Database) -> None:
    survey = await db.get_survey(cb.data.split(":", 1)[1])
    if survey is None:
        await cb.answer("So'rovnoma topilmadi.", show_alert=True)
        return
    count = await db.count_submissions(survey.id)
    if count:
        await cb.answer(
            f"Bu so'rovnomada {count} ta javob bor, shuning uchun o'chirib bo'lmaydi. "
            "«To'xtatish» tugmasidan foydalaning.",
            show_alert=True,
        )
        return
    await _safe_edit(
        cb.message,
        f"🗑 <b>{esc(survey.title)}</b> so'rovnomasini o'chirasizmi?",
        delete_confirm_keyboard(survey.id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm_delok:"))
async def cb_delete_ok(cb: CallbackQuery, db: Database) -> None:
    ok = await db.delete_survey(cb.data.split(":", 1)[1])
    await cb.answer("🗑 O'chirildi" if ok else "O'chirib bo'lmadi (javoblar mavjud).", show_alert=not ok)
    text, kb = await _render_survey_list(db)
    await _safe_edit(cb.message, text, kb)


# =====================================================================
# 3) Statistika
# =====================================================================
@router.message(F.text == Btn.STATS)
@router.message(Command("stats"))
async def show_stats(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    st = await db.stats()
    by_survey: dict[str, list[tuple[str, int]]] = {}
    for g in st["grades"]:
        by_survey.setdefault(g["survey_id"], []).append((g["grade"], g["c"]))

    lines = [
        "📈 <b>Statistika</b>",
        f"👤 Foydalanuvchilar: <b>{st['users']}</b> (botni to'xtatganlar: {st['blocked']})\n",
    ]
    for s in st["surveys"]:
        mark = "🟢" if s["is_active"] else "🔴"
        lines.append(f"{mark} <b>{esc(s['title'])}</b>\n    Javoblar: <b>{s['c']}</b>")
        grades = sorted(by_survey.get(s["id"], []), key=lambda x: grade_key(x[0]))
        if grades:
            lines.append("    " + " • ".join(f"{g}: {c}" for g, c in grades))
    text = "\n".join(lines)
    await message.answer(text[:4000])


# =====================================================================
# 4) Excel hisobot
# =====================================================================
@router.message(F.text == Btn.EXPORT)
@router.message(Command("export"))
async def export_excel(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    wait = await message.answer("⏳ So'rovnoma natijalari Excel faylga tayyorlanmoqda...")
    data = await db.export_data()
    if not data:
        await wait.edit_text("Bazada hozircha to'ldirilgan so'rovnomalar mavjud emas.")
        return
    content = await asyncio.to_thread(build_report, data)  # bot bloklanmasligi uchun
    filename = f"Sorovnoma_hisoboti_{datetime.now(UZ_TZ):%Y-%m-%d}.xlsx"
    await message.answer_document(
        BufferedInputFile(content, filename=filename),
        caption="📊 <b>Maktab so'rovnomalari bo'yicha Excel hisobot</b>\n"
        "<i>Har bir so'rovnoma alohida varaqda, 1-varaq — umumiy jadval.</i>",
    )
    await wait.delete()


# =====================================================================
# 5) E'lon yuborish (/post) — oldindan ko'rish va tasdiqlash bilan
# =====================================================================
def _announcement(text: str) -> str:
    return f"📢 <b>Maktab maslahatchisidan umumiy e'lon:</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}"


@router.message(Command("post"))
async def post_command(message: Message, state: FSMContext, db: Database) -> None:
    body = _strip_command(message.html_text)  # Telegram'dagi qalin/kursiv formatlash saqlanadi
    if not body:
        await message.answer(
            "⚠️ <b>Matn kiritilmadi!</b>\nFoydalanish:\n"
            "<code>/post Barcha o'quvchilar diqqatiga! Ertaga tadbir bo'ladi.</code>"
        )
        return
    text = _announcement(body)
    try:
        await message.answer(text)  # ko'rinishi
    except TelegramBadRequest:
        await message.answer("⚠️ Matnni yuborib bo'lmadi (formatlashda xato bor). Soddaroq yozib ko'ring.")
        return
    recipients = len(await db.get_broadcast_ids())
    await state.set_state(AdminState.confirm_broadcast)
    await state.update_data(broadcast_text=text)
    await message.answer(
        f"👆 Shu e'lon <b>{recipients} ta</b> foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_keyboard(),
    )


async def _send_one(bot: Bot, user_id: int, text: str, db: Database) -> str:
    for _ in range(3):
        try:
            await bot.send_message(user_id, text)
            return "ok"
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            await db.mark_blocked(user_id)
            return "blocked"
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                await db.mark_blocked(user_id)
                return "blocked"
            return "failed"
        except TelegramAPIError:
            return "failed"
    return "failed"


async def _run_broadcast(bot: Bot, db: Database, settings: Settings, text: str, admin_id: int) -> None:
    ids = await db.get_broadcast_ids()
    stats = {"ok": 0, "blocked": 0, "failed": 0}
    for uid in ids:
        stats[await _send_one(bot, uid, text, db)] += 1
        await asyncio.sleep(settings.broadcast_delay)
    await bot.send_message(
        admin_id,
        "✅ <b>E'lon tarqatildi!</b>\n\n"
        f"• Yetkazildi: <b>{stats['ok']}</b>\n"
        f"• Botni to'xtatganlar: <b>{stats['blocked']}</b>\n"
        f"• Boshqa xatolar: <b>{stats['failed']}</b>",
    )


@router.callback_query(AdminState.confirm_broadcast, F.data == "adm_post_ok")
async def broadcast_confirm(cb: CallbackQuery, state: FSMContext, bot: Bot, db: Database, settings: Settings) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text")
    await state.clear()
    if not text:
        await cb.answer("E'lon matni topilmadi.", show_alert=True)
        return
    await _safe_edit(cb.message, "⏳ E'lon yuborilmoqda... Tugagach hisobot keladi.")
    await cb.answer()
    task = asyncio.create_task(_run_broadcast(bot, db, settings, text, cb.from_user.id))
    _background_tasks.add(task)  # GC o'chirib yubormasligi uchun
    task.add_done_callback(_background_tasks.discard)


@router.callback_query(F.data == "adm_post_no")
async def broadcast_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _safe_edit(cb.message, "❌ E'lon yuborish bekor qilindi.")
    await cb.answer()


# =====================================================================
# 6) Bitta foydalanuvchiga xabar (/sms)
# =====================================================================
@router.message(Command("sms"))
async def sms_command(message: Message, bot: Bot, db: Database) -> None:
    parts = _strip_command(message.html_text).split(maxsplit=1)
    if len(parts) < 2 or not parts[0].lstrip("-").isdigit():
        await message.answer(
            "⚠️ <b>Noto'g'ri format!</b>\nFoydalanish:\n<code>/sms 123456789 Xonamga kirib o'tgin</code>"
        )
        return
    target_id, text = int(parts[0]), parts[1]
    try:
        await bot.send_message(
            target_id,
            f"👨‍💼 <b>Maktab maslahatchisidan shaxsiy xabar:</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}",
        )
        await message.answer(f"✅ Xabar <code>{target_id}</code> ga yetkazildi.")
    except TelegramForbiddenError:
        await db.mark_blocked(target_id)
        await message.answer("❌ Foydalanuvchi botni to'xtatgan.")
    except TelegramAPIError as e:
        await message.answer(f"❌ Xabarni yuborib bo'lmadi: {esc(str(e))}")


# =====================================================================
# 7) Murojaatga Reply orqali javob (matn, rasm, ovoz, fayl — hammasi)
# =====================================================================
@router.message(F.reply_to_message)
async def reply_to_user(message: Message, bot: Bot, db: Database) -> None:
    target = await db.get_feedback_target(message.from_user.id, message.reply_to_message.message_id)
    if target is None:
        raise SkipHandler  # bu murojaat emas — boshqa handlerlarga o'tsin
    user_id, name = target
    header = "👨‍💼 <b>Maktab maslahatchisidan javob:</b>\n━━━━━━━━━━━━━━━━━━━━"
    try:
        if message.text:
            await bot.send_message(user_id, f"{header}\n{message.html_text}")
        else:
            await bot.send_message(user_id, header)
            await message.copy_to(user_id)
        await message.reply(f"✅ Javobingiz <b>{esc(name)}</b>ga yuborildi!")
    except TelegramForbiddenError:
        await db.mark_blocked(user_id)
        await message.reply("❌ Javobni yuborib bo'lmadi: foydalanuvchi botni to'xtatgan.")
    except TelegramAPIError as e:
        await message.reply(f"❌ Javobni yuborib bo'lmadi: {esc(str(e))}")


# =====================================================================
# 8) So'rovnoma matnini qabul qilish (holat handlerlari oxirida)
# =====================================================================
@router.message(AdminState.waiting_survey_text, F.text)
async def save_survey(message: Message, state: FSMContext, db: Database, settings: Settings) -> None:
    title, grades, questions, errors = parse_survey_text(message.text)
    if errors:
        shown = "\n".join(f"• {esc(e)}" for e in errors[:8])
        await message.answer(f"⚠️ <b>Matnda xatolar bor:</b>\n{shown}\n\nTuzatib qayta yuboring yoki bekor qiling.")
        return

    survey_id = f"s_{uuid.uuid4().hex[:8]}"
    await db.add_survey(survey_id, title, grades, questions)
    await state.clear()
    await message.answer(
        "✅ <b>Yangi so'rovnoma saqlandi!</b>\n\n"
        f"📌 <b>Nomi:</b> {esc(title)}\n"
        f"👥 <b>Sinflar:</b> {', '.join(map(str, grades))}\n"
        f"❓ <b>Savollar soni:</b> {len(questions)} ta\n\n"
        "O'quvchilar so'rovnomani to'ldirishda sinfiga mos so'rovnomani ko'radi. "
        "Bir sinfga bir nechta so'rovnoma tegishli bo'lsa, tanlash taklif etiladi.",
        reply_markup=main_keyboard(True),
    )


@router.message(AdminState.waiting_survey_text)
async def survey_text_expected(message: Message) -> None:
    await message.answer("⚠️ Iltimos, so'rovnomani matn ko'rinishida yuboring.")
