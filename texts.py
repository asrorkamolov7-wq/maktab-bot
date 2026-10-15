"""Statik matnlar va boshlang'ich so'rovnomalar."""

ABOUT_COUNSELOR = """
👨‍💼 <b>Maktab maslahatchisi kabineti</b>
━━━━━━━━━━━━━━━━━━━━
• <b>F.I.SH:</b> Kamolov Asror
• <b>Lavozimi:</b> Maktab maslahatchisi
• <b>Xona:</b> 2-qavat, Maslahatchi xonasi
• <b>Qabul vaqti:</b> 09:00 dan 16:00 gacha
• <b>Bog'lanish uchun telefon:</b> +998 33 443 55 77

<i>Har qanday shaxsiy masala, kasb tanlash yoki qiyinchiliklar bo'yicha bemalol murojaat qilishingiz mumkin. Barcha suhbatlar to'liq sir saqlanadi.</i>
"""

CLUBS_INFO = """
🎭 <b>Maktabda faoliyat yuritayotgan 7 ta rivojlanish klubi:</b>
━━━━━━━━━━━━━━━━━━━━
1. 🎭 <b>Turon teatr</b> — Sahna madaniyati, aktyorlik mahorati va ijodiy qobiliyatlarni rivojlantirish.
2. 🎵 <b>Iqtidor ansambli</b> — Musiqa, milliy va zamonaviy ijrochilik sanʼati.
3. 📜 <b>Jadidlar izidan</b> — Tarixiy meros, kitobxonlik va maʼrifatparvarlik tadbirlari.
4. 🌿 <b>Eco-schools Uzbekistan</b> — Ekologik savodxonlik, tabiatni asrash va atrof-muhit loyihalari.
5. 🌍 <b>Xorijiy tillar</b> — Chet tillarida erkin muloqot va soʻzlashuv klubi.
6. 🎤 <b>Debat</b> — Notiqlik, tanqidiy fikrlash va munozara madaniyati.
7. 💻 <b>Raqamli avlod qizlari</b> — Qizlar uchun IT, zamonaviy kasblar va media savodxonlik.

<i>Klublarga a'zo bo'lish uchun maktab maslahatchisi xonasiga (2-qavat) murojaat qiling.</i>
"""

COUNCIL_INFO = """
👥 <b>O'quvchilar kengashi tashkiliy tuzilmasi</b>
━━━━━━━━━━━━━━━━━━━━
👑 <b>Kelajak lideri</b>
O'quvchilar kengashi faoliyatiga umumiy rahbarlik qiladi.

📌 <b>Asosiy yo'nalish koordinatorlari va vazifalari:</b>

🎓 <b>Ta'lim koordinatori</b>
Ta'lim sifatini oshirish, fan va til to'garaklarini tashkil etish, o'quvchilarning o'zlashtirishiga yordam berish.

🎭 <b>Madaniyat koordinatori</b>
Maktabning madaniy tadbirlarini tashkil etish, milliy qadriyatlarni targ'ib qilish, "Turon maktab teatri" va "Iqtidor ansambli" faoliyatini qo'llab-quvvatlash.

💻 <b>IT va sun'iy intellekt koordinatori</b>
Raqamli texnologiyalarni targ'ib qilish, IT ko'nikmalarini rivojlantirish, innovatsion loyihalar va tanlovlarni tashkil etish.

🏃‍♂️ <b>Sport koordinatori</b>
Sport tadbirlarini tashkil etish, sog'lom turmush tarzini targ'ib qilish, sport klublari va tanlovlarni rivojlantirish.

🌿 <b>Ekologiya koordinatori</b>
Ekologik loyihalar va aksiyalarni tashkil etish, tabiatni muhofaza qilish, ekologik madaniyatni targ'ib qilish.

📢 <b>Media koordinatori</b>
Maktab hayotini ommaviy axborotda yoritish, ijtimoiy tarmoqlarni yuritish, media loyihalarini tashkil etish.

👥 <b>Ijtimoiy tashabbuslar koordinatori</b>
O'quvchilar tashabbuslarini qo'llab-quvvatlash, ijtimoiy loyihalar va volontyorlik faoliyatini tashkil etish, inklyuziv muhitni rivojlantirish.

━━━━━━━━━━━━━━━━━━━━
👥 <b>5–11-sinf vakillari:</b> Sinf o'quvchilari tomonidan saylanadi.
☘️ <b>Klublar:</b> Maktabda faoliyat yurituvchi tarmoq to'garaklari.
"""

WELCOME = (
    "Assalomu alaykum, <b>{name}</b>!\n\n"
    "🏫 <b>Maktab maslahatchisining rasmiy portaliga xush kelibsiz.</b>\n"
    "Ushbu bot orqali siz o'z qiziqishlaringiz bo'yicha so'rovnomalarda qatnashishingiz, "
    "maktab klublari va kengash faoliyati bilan tanishishingiz hamda "
    "maslahatchiga to'g'ridan-to'g'ri murojaat yo'llashingiz mumkin.\n\n"
    "Kerakli bo'limni tanlang:"
)

SURVEY_TEMPLATE = (
    "Sarlavha: Bitiruvchilar rejalari\n"
    "Sinflar: 9-11\n\n"
    "1. Qaysi sohaga qiziqasiz?\n"
    "- Axborot texnologiyalari (IT)\n"
    "- Tibbiyot\n"
    "- Iqtisodiyot va biznes\n\n"
    "2. Qaysi oliygohga topshirmoqchisiz?\n"
    "[yozma]"
)


def _c(question: str, options: list[str]) -> dict:
    return {"type": "choice", "question": question, "options": options}


def _t(question: str) -> dict:
    return {"type": "text", "question": question, "options": []}


DEFAULT_SURVEYS = [
    {
        "id": "survey_5_8",
        "title": "«Mening qiziqishlarim va kelajakdagi kasbim» (5–8-sinf)",
        "grades": [5, 6, 7, 8],
        "questions": [
            _c("Maktabda qaysi fanlarni o'rganish sizga ko'proq yoqadi?", ["Matematika", "Ona tili va adabiyot", "Tarix", "Chet tili", "Informatika", "Biologiya", "Fizika", "Jismoniy tarbiya", "Musiqa / Tasviriy san'at"]),
            _c("Bo'sh vaqtingizda nimalar bilan shug'ullanishni yoqtirasiz?", ["Kitob o'qish", "Sport", "Rasm chizish", "Kompyuter va IT", "Video / montaj / dizayn", "Qo'shiq / cholg'u", "Pazandachilik / hunar"]),
            _c("O'zingizda qaysi qobiliyat kuchliroq deb o'ylaysiz?", ["Hisoblash va mantiq", "Chiroyli gapirish", "Texnika va kompyuter", "Musiqa va ijod", "Sport", "Tashkilotchilik", "Tinglash va yordam berish", "Hali bilmayman"]),
            _c("Yangi narsani o'rganishda qaysi usul sizga ko'proq yoqadi?", ["O'qib o'rganish", "Amalda bajarib ko'rish", "Video orqali ko'rish", "Ustozdan so'rab", "Do'stlar bilan birgalikda", "Tajriba qilib ko'rish"]),
            _c("Quyidagi faoliyatlardan qaysi biri sizga eng qiziq?", ["Kompyuter / IT", "Tibbiyot", "Texnika va muhandislik", "San'at va ijod", "Sport", "Ta'lim va pedagogika", "Biznes va tadbirkorlik", "Huquq / Harbiy"]),
            _t("Kelajakda qaysi kasb yoki kasblarga qiziqasiz? Nomlarini yozing:"),
            _c("Bu kasbga qiziqishingizga nima sabab bo'lgan?", ["Bu kasb menga yoqadi", "Tanishim shu sohada ishlaydi", "Bolalikdagi orzuim", "Daromadi yaxshi", "Odamlarga yordam berish", "Hali aniq bilmayman"]),
            _c("Siz ko'proq qanday ishni bajarishni xohlaysiz?", ["Odamlar bilan ishlash", "Kompyuter bilan ishlash", "Texnika va qurilmalar", "Hayvonlar va tabiat", "Ijodiy ishlar", "Jamoa bilan ishlash", "Mustaqil ishlash"]),
            _c("Qaysi to'garak yoki klub sizni ko'proq qiziqtiradi?", ["Turon teatr", "Iqtidor ansambli", "Jadidlar izidan", "Eco-schools Uzbekistan", "Xorijiy tillar", "Debat klubi", "Raqamli avlod qizlari"]),
            _t("Maktabda yangi to'garak ochilsa, qaysi yo'nalishda bo'lishini xohlardingiz?"),
            _c("O'zingizni kelajakda qanday inson sifatida tasavvur qilasiz?", ["Yaxshi mutaxassis", "Tadbirkor", "Olim / Tadqiqotchi", "Ijodkor", "Sportchi", "Rahbar", "O'qituvchi"]),
            _c("Sizga kasb tanlashda kimning maslahati ko'proq ta'sir qiladi?", ["Ota-onam", "O'qituvchim", "Sinfdoshlarim / do'stlarim", "Maktab maslahatchisi", "O'zim mustaqil tanlayman"]),
            _t("Kelajakdagi qaysi kasb haqida ko'proq ma'lumot olishni xohlaysiz?"),
            _t("Siz maktab hayotini yaxshilash uchun qanday yangi taklif bera olasiz?"),
            _t("O'zingiz haqingizda biz bilishimiz kerak bo'lgan boshqa qiziqishingiz bormi?"),
        ],
    },
    {
        "id": "survey_9_11",
        "title": "«Kasb tanlash va oliygohga tayyorgarlik» (9–11-sinf)",
        "grades": [9, 10, 11],
        "questions": [
            _c("Kelajakda qaysi kasb egasi bo'lishni xohlaysiz?", ["Tibbiyot", "Muhandislik / Arxitektura", "IT sohasi", "Iqtisodiyot / Biznes", "Ta'lim / Pedagogika", "Huquqshunoslik", "Harbiy soha", "Boshqa"]),
            _c("Sizni qaysi fanlar ko'proq qiziqtiradi?", ["Matematika", "Fizika", "Kimyo / Biologiya", "Ingliz tili / Chet tillari", "Tarix va huquq", "Ona tili va adabiyot"]),
            _c("Maktabni tugatgach o'qishni davom ettirishni rejalashtiryapsizmi?", ["Ha, albatta", "Yo'q", "Hali aniq emas"]),
            _c("Qayerda o'qishni xohlaysiz?", ["O'zbekiston oliy ta'lim muassasalarida", "Xorijiy davlat universitetlarida", "Ikkalasini ham ko'rib chiqyapman"]),
            _c("Qaysi davlat universitetlarida o'qish sizni qiziqtiradi?", ["O'zbekiston", "AQSh", "Buyuk Britaniya", "Koreya", "Turkiya", "Yevropa davlatlari", "Rossiya"]),
            _c("Xorijiy universitetlarga hujjat topshirishni rejalashtiryapsizmi?", ["Ha", "Yo'q", "Hali o'ylab ko'ryapman"]),
            _c("Qaysi xalqaro test yoki sertifikatlarga tayyorlanyapsiz?", ["IELTS", "SAT", "CEFR", "TOEFL", "Hali boshlamaganman"]),
            _c("Ingliz tilini bilish darajangiz qanday?", ["Boshlang'ich", "O'rta", "Yaxshi (B2 daraja)", "Juda yaxshi (C1 daraja)"]),
            _t("Hozirda qaysi to'garak yoki o'quv markazlariga qatnashyapsiz?"),
            _c("Siz qaysi sohada o'zingizni rivojlantirishni xohlaysiz?", ["Akademik bilimlar", "Liderlik ko'nikmalari", "Ilmiy izlanish", "Sport", "Ijodiy yo'nalishlar"]),
            _c("Universitetga kirish uchun sizga birinchi navbatda qanday yordam kerak?", ["Testlarga tayyorgarlik", "Universitet tanlashda maslahat", "Hujjat topshirish tartibi", "Grant imkoniyatlari"]),
            _t("Kelajakdagi asosiy maqsadingiz nima? Qisqacha yozing:"),
            _c("Agar chet elda o'qish imkoniyati yaratilsa, undan foydalanishga tayyormisiz?", ["Ha, albatta", "Ehtimol", "Yo'q"]),
            _c("Maktab maslahatchisi bilan suhbatlashishni xohlaysizmi?", ["Ha, suhbatlashmoqchiman", "Hozircha yo'q"]),
            _t("Maktab hayotini yaxshilash uchun qanday taklifingiz bor?"),
        ],
    },
]
