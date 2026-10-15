# Maktab maslahatchisi boti

Telegram bot (aiogram 3): sinflar bo'yicha so'rovnomalar, maslahatchiga murojaat,
klublar va o'quvchilar kengashi haqida ma'lumot, admin paneli va Excel hisobot.

## Ishga tushirish

```bash
pip install -r requirements.txt
export BOT_TOKEN="..."        # @BotFather -> /revoke bilan olingan YANGI token
export ADMIN_IDS="123456789"  # bir nechta bo'lsa: 111,222
python main.py
```

| O'zgaruvchi | Majburiy | Izoh |
|---|---|---|
| `BOT_TOKEN` | ha | Bot tokeni (kodga yozilmaydi) |
| `ADMIN_IDS` | ha | Adminlar Telegram ID'lari (eski `ADMIN_ID` ham ishlaydi) |
| `DB_PATH` | yo'q | Standart: `data/school_bot.db` |
| `PORT` | yo'q | Health-check porti (standart 10000) |
| `GRADE_LETTERS` | yo'q | Standart: `A,B,V,G,D` |

## Render'da joylash

1. **Start command:** `python main.py`
2. **Environment** bo'limida `BOT_TOKEN` va `ADMIN_IDS` ni kiriting.
3. **Muhim:** Renderning bepul disk'i vaqtincha. Javoblar yo'qolmasligi uchun
   Persistent Disk ulang (masalan `/var/data`) va `DB_PATH=/var/data/school_bot.db` qo'ying.
   Aks holda har deploydan keyin baza tozalanadi. Hech bo'lmasa Excel hisobotni muntazam yuklab oling.
4. Bepul tarifda servis uxlab qolmasligi uchun UptimeRobot kabi xizmat bilan
   `https://<servis>.onrender.com/health` manzilini har 5 daqiqada tekshirtiring.

## Admin buyruqlari

| Buyruq / tugma | Vazifasi |
|---|---|
| ➕ Yangi so'rovnoma / `/add_survey` | Bitta xabar bilan so'rovnoma qo'shish (namuna botda ko'rsatiladi) |
| 📋 So'rovnomalar / `/surveys` | Yoqish/to'xtatish, javobsiz so'rovnomani o'chirish |
| 📈 Statistika / `/stats` | Foydalanuvchilar va javoblar soni, sinflar kesimida |
| 📊 Excel / `/export` | Har so'rovnoma alohida varaqda + umumiy varaq |
| `/post matn` | Oldindan ko'rish va tasdiqlashdan keyin hammaga e'lon |
| `/sms ID matn` | Bitta foydalanuvchiga xabar |
| Murojaatga **Reply** | Matn, rasm, ovoz yoki fayl bilan javob |

## Tuzilma

```
main.py                 # kirish nuqtasi
app/
  config.py             # muhit o'zgaruvchilari
  database.py           # SQLite (bitta ulanish, WAL, tranzaksiyalar)
  models.py texts.py    # modellar, statik matnlar, boshlang'ich so'rovnomalar
  survey_parser.py      # admin matnini so'rovnomaga aylantirish + xato xabarlari
  excel_report.py       # openpyxl hisobot (pandas kerak emas)
  keyboards.py states.py filters.py middlewares.py utils.py web.py
  handlers/
    menu.py             # menyu (birinchi ulanadi: har holatda ishlaydi)
    admin.py            # admin paneli
    survey.py support.py fallback.py
tests/test_parser.py    # pytest
```

## Eski versiyadan o'tish

- Eski `custom_surveys` jadvalidagi so'rovnomalar avtomatik ko'chiriladi.
- Eski `answers` jadvali o'zgarmaydi, lekin yangi Excel hisobotga kirmaydi.
  O'tishdan oldin eski botdan hisobotni yuklab oling.
