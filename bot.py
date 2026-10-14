import asyncio
import os
import aiosqlite
import pandas as pd
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)

# ================= SOZLAMALAR =================
BOT_TOKEN = "8619703357:AAHIGSxKdB2k2Lw643-WzsIOQf_OrGoUgTE"
ADMIN_ID = 7680698926
DB_NAME = "school_bot.db"

# ================= BO'LIMLAR MATNLARI =================
ABOUT_COUNSELOR = """
👨‍🏫 **Maktab maslahatchisi haqida ma'lumot:**

• **F.I.SH:** Kamolov Asror
• **Lavozimi:** Maktab maslahatchisi
• **Qabul kunlari:** Dushanba - Juma (08:30 - 16:00)
• **Xona:** 2-qavat, Maslahatchi va psixologik xizmat xonasi

*Eslatma: Har qanday savol, muammo, kasb tanlash yoki shaxsiy masalalar bo'yicha bemalol murojaat qilishingiz mumkin. Barcha suhbatlar sir saqlanadi!*
"""

CLUBS_INFO = """
🎯 **Maktab maslahatchisi qoshidagi 7 ta klub:**

1. 🌟 **"Yosh liderlar" klubi** – Yetakchilik qobiliyatini rivojlantirish.
2. 📚 **"Kitobxonlar" klubi** – Mutolaa madaniyati va kitobxonlik bahslari.
3. 🎤 **"Notiqlik va debat" klubi** – Ommaviy nutq va o'z fikrini erkin ifodalash.
4. 🧠 **"Psixologik salomatlik" klubi** – Stressni yengish va o'ziga ishonch.
5. 💼 **"Kelajak kasblari" klubi** – Zamonaviy kasblar va oliygohlarga yo'naltirish.
6. 🎨 **"Ijodkor yoshlar" klubi** – Rassomchilik, adabiyot va ijodiy ishlar.
7. 🤝 **"Tengdosh-tengdoshga" ko'ngillilar klubi** – O'zaro yordam va do'stlik.

*Klublarga a'zo bo'lish uchun maktab maslahatchisi xonasiga murojaat qiling.*
"""

COUNCIL_INFO = """
👥 **Maktab o'quvchilar kengashi (Koordinatorlar):**

• **Kengash raisi:** Maktab sardori
• **Ta'lim yo'nalishi koordinatori:** Iqtidorli o'quvchilar bilan ishlash
• **Intizom va davomat koordinatori:** Odob-axloq va tartib-intizom
• **Madaniy-ma'rifiy ishlar koordinatori:** Tadbirlar va to'garaklar
• **Sport va salomatlik koordinatori:** Musobaqalar va sog'lom turmush tarzi
• **Matbuot va media koordinatori:** Maktab yangiliklari va devoriy gazetalar
"""

# ================= SO'ROVNOMALAR RO'YXATI =================
SURVEYS = [
    {
        "id": "kasb_9_11",
        "title": "🎯 Kasbga yo'naltirish so'rovnomasi",
        "grades": [9, 10, 11],
        "questions": [
            {
                "question": "Kelajakda qaysi sohani tanlashni rejalashtiryapsiz?",
                "options": ["Axborot texnologiyalari (IT)", "Tibbiyot / Biologiya", "Iqtisodiyot / Biznes", "Pedagogika / Ta'lim", "Harbiy / Huquqshunoslik"]
            },
            {
                "question": "Kasb tanlashda sizga kim eng ko'p ta'sir qilmoqda?",
                "options": ["O'z shaxsiy qiziqishim", "Ota-onam va oilam", "Ustozlarim", "Do'stlarim / Internet"]
            },
            {
                "question": "Kelajakdagi maqsadlaringiz bo'yicha maslahatchi bilan suhbatlashmoqchimisiz?",
                "options": ["Ha, suhbatlashmoqchiman", "Hozircha yo'q, o'zim bilaman"]
            }
        ]
    },
    {
        "id": "moslashuv_5_8",
        "title": "🤝 Darslarga qiziqish va muhit so'rovnomasi",
        "grades": [5, 6, 7, 8],
        "questions": [
            {
                "question": "Maktabda o'zingizni qanday his qilasiz?",
                "options": ["Juda xursand va erkin", "Yaxshi", "Ba'zida zerikarli", "Qiynalyapman"]
            },
            {
                "question": "Sinfdoshlaringiz bilan munosabatingiz qanday?",
                "options": ["Juda ahil va do'stona", "O'rtacha, faqat ayrimlar bilan", "Yakka bo'lishni yoqtiraman"]
            },
            {
                "question": "Maktab maslahatchisi klublariga qatnashishni xohlaysizmi?",
                "options": ["Ha, albatta", "Qaysi klubligiga qarab", "Yo'q"]
            }
        ]
    },
    {
        "id": "umumiy_1_4",
        "title": "🏫 Maktab hayoti so'rovnomasi",
        "grades": [1, 2, 3, 4],
        "questions": [
            {
                "question": "Maktabga kelish sizga yoqadimi?",
                "options": ["Ha, juda yoqadi 😊", "Ba'zida 🙂", "Yo'q 😔"]
            },
            {
                "question": "Eng yoqtirgan mashg'ulotingiz nima?",
                "options": ["Kitob o'qish", "Rasm chizish", "Sport bilan shug'ullanish", "Kompyuter/Telefon"]
            }
        ]
    }
]

# ================= HOLATLAR (FSM) =================
class SurveyProcess(StatesGroup):
    waiting_fio = State()
    waiting_grade_num = State()
    waiting_grade_letter = State()
    choosing_survey = State()
    answering_questions = State()

# ================= BAZANI ISHGA TUSHIRISH =================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                grade TEXT,
                survey_title TEXT,
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ================= TUGMALAR =================
def get_main_keyboard(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="📝 So'rovnomalar"), KeyboardButton(text="🎯 Klublar")],
        [KeyboardButton(text="👥 O'quvchilar kengashi"), KeyboardButton(text="👨‍🏫 Maktab maslahatchisi")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="📊 Excel hisobotni yuklash")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_grade_num_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=f"{i}-sinf", callback_data=f"gnum_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(text=f"{i}-sinf", callback_data=f"gnum_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(text=f"{i}-sinf", callback_data=f"gnum_{i}") for i in range(9, 12)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_grade_letter_keyboard():
    letters = ["A", "B", "V", "G"]
    keyboard = [[InlineKeyboardButton(text=l, callback_data=f"glet_{l}") for l in letters]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ================= BOT ISH BOSHLANISHI =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n"
        "Maktab maslahatchisining rasmiy axborot va so'rovnoma botiga xush kelibsiz.\n\n"
        "Quyidagi menyulardan birini tanlang:",
        reply_markup=get_main_keyboard(is_admin)
    )

# ================= ASOSIY BO'LIMLAR =================
@dp.message(F.text == "🎯 Klublar")
async def show_clubs(message: Message):
    await message.answer(CLUBS_INFO)

@dp.message(F.text == "👥 O'quvchilar kengashi")
async def show_council(message: Message):
    await message.answer(COUNCIL_INFO)

@dp.message(F.text == "👨‍🏫 Maktab maslahatchisi")
async def show_counselor(message: Message):
    await message.answer(ABOUT_COUNSELOR)

# ================= SO'ROVNOMA ZANJIRI =================
@dp.message(F.text == "📝 So'rovnomalar")
async def start_survey_flow(message: Message, state: FSMContext):
    await message.answer(
        "So'rovnomani to'ldirish uchun avval Ism, Familiya va Sharifingizni kiriting:\n"
        "(Masalan: Soliyev Sardor Anvar o'g'li)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SurveyProcess.waiting_fio)

@dp.message(SurveyProcess.waiting_fio)
async def process_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    await state.update_data(fio=fio)
    await message.answer(
        f"Rahmat, {fio}!\nEndi sinfingizni tanlang:",
        reply_markup=get_grade_num_keyboard()
    )
    await state.set_state(SurveyProcess.waiting_grade_num)

@dp.callback_query(SurveyProcess.waiting_grade_num, F.data.startswith("gnum_"))
async def process_gnum(callback: CallbackQuery, state: FSMContext):
    gnum = int(callback.data.split("_")[1])
    await state.update_data(grade_num=gnum)
    await callback.message.edit_text(
        f"{gnum}-sinf tanlandi. Endi sinf harfini tanlang:",
        reply_markup=get_grade_letter_keyboard()
    )
    await state.set_state(SurveyProcess.waiting_grade_letter)
    await callback.answer()

@dp.callback_query(SurveyProcess.waiting_grade_letter, F.data.startswith("glet_"))
async def process_glet(callback: CallbackQuery, state: FSMContext):
    glet = callback.data.split("_")[1]
    data = await state.get_data()
    gnum = data['grade_num']
    full_grade = f"{gnum}-{glet}"
    await state.update_data(full_grade=full_grade)

    available_surveys = [s for s in SURVEYS if gnum in s["grades"]]

    if not available_surveys:
        is_admin = (callback.from_user.id == ADMIN_ID)
        await callback.message.delete()
        await callback.message.answer(
            f"{full_grade}-sinf uchun hozirda faol so'rovnomalar mavjud emas.",
            reply_markup=get_main_keyboard(is_admin)
        )
        await state.clear()
        await callback.answer()
        return

    keyboard = []
    for s in available_surveys:
        keyboard.append([InlineKeyboardButton(text=s["title"], callback_data=f"sel_surv_{s['id']}")])

    await callback.message.edit_text(
        f"Sinfingiz: {full_grade}\nO'zingizga mos so'rovnomani tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(SurveyProcess.choosing_survey)
    await callback.answer()

@dp.callback_query(SurveyProcess.choosing_survey, F.data.startswith("sel_surv_"))
async def process_survey_choice(callback: CallbackQuery, state: FSMContext):
    surv_id = callback.data.replace("sel_surv_", "")
    selected_survey = next(s for s in SURVEYS if s["id"] == surv_id)

    await state.update_data(
        current_survey=selected_survey,
        question_idx=0,
        collected_answers=[]
    )

    first_q = selected_survey["questions"][0]
    keyboard = [[InlineKeyboardButton(text=opt, callback_data=f"ans_{opt[:25]}")] for opt in first_q["options"]]

    await callback.message.edit_text(
        f"📋 {selected_survey['title']}\n\n1-savol: {first_q['question']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(SurveyProcess.answering_questions)
    await callback.answer()

@dp.callback_query(SurveyProcess.answering_questions, F.data.startswith("ans_"))
async def process_question_answer(callback: CallbackQuery, state: FSMContext):
    chosen_opt = callback.data.replace("ans_", "")
    data = await state.get_data()
    survey = data["current_survey"]
    q_idx = data["question_idx"]
    collected = data["collected_answers"]

    current_q_text = survey["questions"][q_idx]["question"]
    collected.append((current_q_text, chosen_opt))
    q_idx += 1

    if q_idx < len(survey["questions"]):
        await state.update_data(question_idx=q_idx, collected_answers=collected)
        next_q = survey["questions"][q_idx]
        keyboard = [[InlineKeyboardButton(text=opt, callback_data=f"ans_{opt[:25]}")] for opt in next_q["options"]]

        await callback.message.edit_text(
            f"📋 {survey['title']}\n\n{q_idx + 1}-savol: {next_q['question']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        user_id = callback.from_user.id
        fio = data["fio"]
        grade = data["full_grade"]
        survey_title = survey["title"]

        async with aiosqlite.connect(DB_NAME) as db:
            for q_text, ans_text in collected:
                await db.execute(
                    "INSERT INTO answers (user_id, full_name, grade, survey_title, question, answer) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, fio, grade, survey_title, q_text, ans_text)
                )
            await db.commit()

        await state.clear()
        is_admin = (user_id == ADMIN_ID)
        await callback.message.delete()
        await callback.message.answer(
            f"✅ Rahmat, {fio}!\nSizning javoblaringiz maslahatchiga muvaffaqiyatli yetkazildi.",
            reply_markup=get_main_keyboard(is_admin)
        )
    await callback.answer()

# ================= ADMIN UCHUN EXCEL HISOBOT =================
@dp.message(F.text == "📊 Excel hisobotni yuklash")
async def send_excel_report(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Ushbu bo'lim faqat maktab maslahatchisi uchun ochiq!")
        return

    await message.answer("⏳ So'rovnoma natijalari Excel faylga jamlanmoqda...")

    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT grade AS "Sinf", full_name AS "F.I.SH", survey_title AS "So'rovnoma",
                   question AS "Savol", answer AS "Javob", created_at AS "To'ldirilgan vaqt"
            FROM answers
            ORDER BY grade ASC, full_name ASC, id ASC
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            cols = [col[0] for col in cursor.description]

    if not rows:
        await message.answer("Bazada hozircha to'ldirilgan so'rovnomalar mavjud emas.")
        return

    df = pd.DataFrame(rows, columns=cols)
    file_path = "Maktab_Sorovnoma_Hisoboti.xlsx"

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Umumiy barcha sinflar", index=False)
        for grade in df["Sinf"].unique():
            grade_df = df[df["Sinf"] == grade]
            sheet_title = str(grade).replace("/", "-")[:30]
            grade_df.to_excel(writer, sheet_name=sheet_title, index=False)

    doc = FSInputFile(file_path)
    await message.answer_document(
        doc,
        caption="📊 Barcha sinflar bo'yicha to'liq hisobot fayli."
    )

    if os.path.exists(file_path):
        os.remove(file_path)

# ================= ISHGA TUSHIRISH =================
async def main():
    await init_db()
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
