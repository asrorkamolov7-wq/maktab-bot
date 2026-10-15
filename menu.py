"""Asosiy menyu. Bu router BIRINCHI ulanadi: menyu tugmalari har qanday holatda
(so'rovnoma yoki murojaat o'rtasida ham) ishlaydi va javob sifatida saqlanib qolmaydi."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from database import Database
from keyboards import Btn, cancel_keyboard, main_keyboard
from states import SupportState, SurveyState
from texts import ABOUT_COUNSELOR, CLUBS_INFO, COUNCIL_INFO, WELCOME
from utils import esc

router = Router(name="menu")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    user = message.from_user
    await message.answer(
        WELCOME.format(name=esc(user.full_name)),
        reply_markup=main_keyboard(user.id in settings.admin_ids),
    )


@router.message(Command("cancel"))
@router.message(F.text == Btn.CANCEL)
async def cancel_any(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    await message.answer(
        "Jarayon bekor qilindi va asosiy menyuga qaytdingiz.",
        reply_markup=main_keyboard(message.from_user.id in settings.admin_ids),
    )


@router.callback_query(F.data == "cancel_survey")
async def cancel_survey_cb(cb: CallbackQuery, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass
    await cb.message.answer(
        "So'rovnoma bekor qilindi va asosiy menyuga qaytdingiz.",
        reply_markup=main_keyboard(cb.from_user.id in settings.admin_ids),
    )
    await cb.answer()


@router.message(F.text == Btn.COUNSELOR)
async def show_counselor(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ABOUT_COUNSELOR)


@router.message(F.text == Btn.CLUBS)
async def show_clubs(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(CLUBS_INFO)


@router.message(F.text == Btn.COUNCIL)
async def show_council(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(COUNCIL_INFO)


@router.message(F.text == Btn.SURVEY)
async def start_survey(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    if not await db.has_active_surveys():
        await message.answer("Hozircha faol so'rovnoma mavjud emas. Keyinroq qayta urinib ko'ring.")
        return
    await message.answer(
        "📝 <b>So'rovnomani to'ldirish uchun avval Ism va Familiyangizni kiriting:</b>\n"
        "<i>(Masalan: Karimov Jasur)</i>\n\n"
        "<i>Jarayonni to'xtatish uchun «❌ Bekor qilish» tugmasini bosing.</i>",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(SurveyState.waiting_fio)


@router.message(F.text == Btn.SUPPORT)
async def start_support(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "✍️ <b>Maslahatchiga yo'llamoqchi bo'lgan savol yoki murojaatingizni yozing:</b>\n\n"
        "<i>Matn, rasm, ovozli xabar yoki fayl yuborishingiz mumkin. Xabaringiz maslahatchiga "
        "yetkaziladi va javob shu bot orqali qaytariladi. Bekor qilish uchun pastdagi tugmani bosing.</i>",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(SupportState.waiting_message)
