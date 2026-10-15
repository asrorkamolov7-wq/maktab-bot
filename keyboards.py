"""Barcha klaviaturalar va tugma matnlari."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from models import Question, Survey


class Btn:
    SURVEY = "📝 So'rovnomani to'ldirish"
    SUPPORT = "✉️ Maslahatchiga murojaat"
    CLUBS = "🎭 7 ta rivojlanish klubi"
    COUNCIL = "👥 O'quvchilar kengashi"
    COUNSELOR = "👨‍💼 Maktab maslahatchisi"
    CANCEL = "❌ Bekor qilish"
    # admin (matnlar eski versiya bilan bir xil: eski klaviaturalar ham ishlaydi)
    ADD_SURVEY = "➕ Yangi so'rovnoma qo'shish"
    SURVEYS = "📋 So'rovnomalar"
    STATS = "📈 Statistika"
    EXPORT = "📊 Excel hisobotni yuklash"


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=Btn.SURVEY)],
        [KeyboardButton(text=Btn.SUPPORT)],
        [KeyboardButton(text=Btn.CLUBS), KeyboardButton(text=Btn.COUNCIL)],
        [KeyboardButton(text=Btn.COUNSELOR)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=Btn.ADD_SURVEY), KeyboardButton(text=Btn.SURVEYS)])
        rows.append([KeyboardButton(text=Btn.STATS), KeyboardButton(text=Btn.EXPORT)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Btn.CANCEL)]], resize_keyboard=True
    )


def _cancel_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=Btn.CANCEL, callback_data="cancel_survey")]


def grade_num_keyboard() -> InlineKeyboardMarkup:
    def b(n: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=f"{n}-sinf", callback_data=f"num:{n}")

    return InlineKeyboardMarkup(
        inline_keyboard=[[b(5), b(6), b(7)], [b(8), b(9)], [b(10), b(11)], _cancel_row()]
    )


def grade_letter_keyboard(letters: tuple[str, ...]) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=x, callback_data=f"let:{x}") for x in letters]
    return InlineKeyboardMarkup(inline_keyboard=[row, _cancel_row()])


def survey_pick_keyboard(surveys: list[Survey]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=s.title[:60], callback_data=f"pick:{s.id}")] for s in surveys]
    rows.append(_cancel_row())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_keyboard(q_idx: int, question: Question) -> InlineKeyboardMarkup:
    """callback: ans:<savol_indeksi>:<variant_indeksi> (64 bayt limitidan xavfsiz)"""
    rows = [
        [InlineKeyboardButton(text=opt, callback_data=f"ans:{q_idx}:{i}")]
        for i, opt in enumerate(question.options)
    ]
    rows.append([InlineKeyboardButton(text="❌ So'rovnomani to'xtatish", callback_data="cancel_survey")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="adm_post_ok"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_post_no"),
            ]
        ]
    )


def surveys_admin_keyboard(items: list[tuple[Survey, int]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for n, (s, _count) in enumerate(items, start=1):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{n}. " + ("⏸ To'xtatish" if s.is_active else "▶️ Yoqish"),
                    callback_data=f"adm_tg:{s.id}",
                ),
                InlineKeyboardButton(text=f"{n}. 🗑 O'chirish", callback_data=f"adm_del:{s.id}"),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirm_keyboard(survey_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Ha, o'chirish", callback_data=f"adm_delok:{survey_id}"),
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_list"),
            ]
        ]
    )
