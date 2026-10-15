"""So'rovnomani to'ldirish jarayoni (FSM)."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from database import Database
from keyboards import (
    grade_letter_keyboard,
    grade_num_keyboard,
    main_keyboard,
    question_keyboard,
    survey_pick_keyboard,
)
from models import Survey
from states import SurveyState
from utils import esc, progress_bar

logger = logging.getLogger(__name__)

router = Router(name="survey")
router.message.filter(F.chat.type == "private")

MAX_TEXT_ANSWER = 1000


# ---------------- yordamchi funksiyalar ----------------
def _valid_fio(fio: str) -> bool:
    return 5 <= len(fio) <= 80 and len(fio.split()) >= 2 and not any(ch.isdigit() for ch in fio)


async def _send_question(bot: Bot, chat_id: int, survey: Survey, idx: int) -> None:
    q = survey.questions[idx]
    total = len(survey.questions)
    text = (
        f"📊 <b>Savol {idx + 1}/{total}</b>  {progress_bar(idx, total)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n<b>{esc(q.text)}</b>"
    )
    if q.type == "choice":
        await bot.send_message(chat_id, text, reply_markup=question_keyboard(idx, q))
    else:
        await bot.send_message(chat_id, text + "\n\n✍️ <i>Javobingizni xabar sifatida yozib yuboring:</i>")


async def _begin(bot: Bot, chat_id: int, state: FSMContext, survey: Survey) -> None:
    await state.update_data(survey_id=survey.id, q_idx=0, answers=[])
    await state.set_state(SurveyState.answering)
    await _send_question(bot, chat_id, survey, 0)


async def _advance(bot: Bot, db: Database, settings: Settings, state: FSMContext, user_id: int, answer: str) -> None:
    data = await state.get_data()
    survey = await db.get_survey(data["survey_id"])
    keyboard = main_keyboard(user_id in settings.admin_ids)
    if survey is None:
        await state.clear()
        await bot.send_message(user_id, "Bu so'rovnoma o'chirib yuborilgan.", reply_markup=keyboard)
        return

    answers = [*data["answers"], answer]
    if len(answers) < len(survey.questions):
        await state.update_data(q_idx=len(answers), answers=answers)
        await _send_question(bot, user_id, survey, len(answers))
        return

    fio = data["fio"]
    saved = await db.save_submission(survey, user_id, fio, data["full_grade"], answers)
    await state.clear()
    if saved:
        await bot.send_message(
            user_id,
            f"✅ <b>Katta rahmat, {esc(fio)}!</b>\n\n"
            "Siz so'rovnomani to'liq yakunladingiz. Barcha javoblaringiz maslahatchiga yetkazildi.",
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(user_id, "Siz bu so'rovnomani allaqachon to'ldirgansiz.", reply_markup=keyboard)


# ---------------- F.I.SH ----------------
@router.message(SurveyState.waiting_fio, F.text)
async def process_fio(message: Message, state: FSMContext) -> None:
    fio = " ".join(message.text.split())
    if not _valid_fio(fio):
        await message.answer(
            "⚠️ Iltimos, ism va familiyangizni to'liq (raqamsiz) yozing.\n<i>Masalan: Karimov Jasur</i>"
        )
        return
    await state.update_data(fio=fio)
    await state.set_state(SurveyState.waiting_grade_num)
    await message.answer(f"Rahmat, <b>{esc(fio)}</b>!\nEndi sinfingizni tanlang:", reply_markup=grade_num_keyboard())


# ---------------- sinf ----------------
@router.callback_query(SurveyState.waiting_grade_num, F.data.startswith("num:"))
async def process_grade_num(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    grade_num = int(cb.data.split(":")[1])
    if not 5 <= grade_num <= 11:
        await cb.answer()
        return
    await state.update_data(grade_num=grade_num)
    await state.set_state(SurveyState.waiting_grade_letter)
    await cb.message.edit_text(
        f"Tanlandi: <b>{grade_num}-sinf</b>\nSinfingiz harfini tanlang:",
        reply_markup=grade_letter_keyboard(settings.grade_letters),
    )
    await cb.answer()


@router.callback_query(SurveyState.waiting_grade_letter, F.data.startswith("let:"))
async def process_grade_letter(
    cb: CallbackQuery, state: FSMContext, bot: Bot, db: Database, settings: Settings
) -> None:
    letter = cb.data.split(":", 1)[1]
    data = await state.get_data()
    grade_num = data["grade_num"]
    full_grade = f"{grade_num}-{letter}"
    await state.update_data(full_grade=full_grade)

    available, any_active = await db.surveys_for_grade(grade_num, cb.from_user.id)
    keyboard = main_keyboard(cb.from_user.id in settings.admin_ids)

    if not available:
        try:
            await cb.message.delete()
        except TelegramBadRequest:
            pass
        text = (
            "Siz bu sinf uchun mavjud barcha so'rovnomalarni allaqachon to'ldirgansiz. Rahmat! 🙏"
            if any_active
            else f"{grade_num}-sinf uchun hozircha faol so'rovnoma mavjud emas."
        )
        await state.clear()
        await bot.send_message(cb.from_user.id, text, reply_markup=keyboard)
        await cb.answer()
        return

    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass

    if len(available) == 1:
        await _begin(bot, cb.from_user.id, state, available[0])
    else:
        await state.set_state(SurveyState.waiting_survey_pick)
        await bot.send_message(
            cb.from_user.id,
            f"<b>{esc(full_grade)}</b> sinfi uchun bir nechta so'rovnoma mavjud. Birini tanlang:",
            reply_markup=survey_pick_keyboard(available),
        )
    await cb.answer()


@router.callback_query(SurveyState.waiting_survey_pick, F.data.startswith("pick:"))
async def process_pick(cb: CallbackQuery, state: FSMContext, bot: Bot, db: Database) -> None:
    survey = await db.get_survey(cb.data.split(":", 1)[1])
    if survey is None or not survey.is_active:
        await cb.answer("Bu so'rovnoma endi mavjud emas.", show_alert=True)
        return
    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass
    await _begin(bot, cb.from_user.id, state, survey)
    await cb.answer()


# ---------------- savollarga javob ----------------
@router.callback_query(SurveyState.answering, F.data.startswith("ans:"))
async def handle_choice(cb: CallbackQuery, state: FSMContext, bot: Bot, db: Database, settings: Settings) -> None:
    try:
        _, q_s, o_s = cb.data.split(":")
        q_pos, opt_pos = int(q_s), int(o_s)
    except ValueError:
        await cb.answer()
        return

    data = await state.get_data()
    survey = await db.get_survey(data["survey_id"])
    if survey is None:
        await state.clear()
        await cb.answer("So'rovnoma topilmadi.", show_alert=True)
        return
    if q_pos != data["q_idx"]:
        await cb.answer("Bu savolga allaqachon javob berilgan.")
        return

    question = survey.questions[q_pos]
    if question.type != "choice" or not 0 <= opt_pos < len(question.options):
        await cb.answer()
        return

    answer = question.options[opt_pos]
    try:  # tanlangan javobni xabarda qoldirib, tugmalarni olib tashlaymiz
        await cb.message.edit_text(f"<b>{esc(question.text)}</b>\n\n✅ {esc(answer)}", reply_markup=None)
    except TelegramBadRequest:
        pass
    await cb.answer()
    await _advance(bot, db, settings, state, cb.from_user.id, answer)


@router.message(SurveyState.answering, F.text)
async def handle_text(message: Message, state: FSMContext, bot: Bot, db: Database, settings: Settings) -> None:
    data = await state.get_data()
    survey = await db.get_survey(data["survey_id"])
    if survey is None:
        await state.clear()
        await message.answer("Bu so'rovnoma o'chirib yuborilgan.", reply_markup=main_keyboard(message.from_user.id in settings.admin_ids))
        return

    question = survey.questions[data["q_idx"]]
    if question.type == "choice":
        await message.answer("👆 Iltimos, yuqoridagi tugmalardan birini tanlang.")
        return

    answer = message.text.strip()
    if len(answer) > MAX_TEXT_ANSWER:
        await message.answer(f"⚠️ Javob juda uzun. Iltimos, {MAX_TEXT_ANSWER} belgidan qisqaroq yozing.")
        return
    await _advance(bot, db, settings, state, message.from_user.id, answer)


# ---------------- noto'g'ri turdagi kiritish ----------------
@router.message(StateFilter(SurveyState.waiting_fio, SurveyState.answering))
async def expect_text(message: Message) -> None:
    await message.answer("⚠️ Iltimos, javobni oddiy matn ko'rinishida yuboring.")


@router.message(
    StateFilter(SurveyState.waiting_grade_num, SurveyState.waiting_grade_letter, SurveyState.waiting_survey_pick)
)
async def expect_button(message: Message) -> None:
    await message.answer("👆 Iltimos, yuqoridagi tugmalardan birini tanlang.")
