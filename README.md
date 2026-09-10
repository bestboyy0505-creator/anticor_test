# Test Bot — Telegram

5 ta variant, har birida 25 tadan savol. Foydalanuvchi variant tanlaydi,
savollarga tugmalar orqali javob beradi, oxirida necha ta to'g'ri va necha
foiz ekani chiqadi.

## Fayllar
- `bot.py` — botning asosiy kodi
- `questions.json` — savollar, variantlar va to'g'ri javoblar
- `requirements.txt` — kerakli kutubxonalar

## 1-qadam: Bot yaratish (BotFather)
1. Telegramda **@BotFather** ga yozing.
2. `/newbot` buyrug'ini yuboring, botga nom va username bering.
3. Sizga **token** beradi (masalan: `123456:ABC-DEF...`) — shuni saqlab qo'ying, hech kimga bermang.

## 2-qadam: Bepul hostingga joylashtirish (Render.com)
1. https://render.com da bepul akkaunt oching (GitHub orqali kirish qulay).
2. Shu papkadagi fayllarni (`bot.py`, `questions.json`, `requirements.txt`)
   GitHub'da yangi repository qilib yuklang.
3. Render'da **New → Web Service** tugmasini bosing, o'sha repository'ni tanlang.
4. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Environment Variable:** `BOT_TOKEN` = (BotFather bergan tokeningiz)
5. "Create Web Service" bosing — Render avtomatik ishga tushiradi.

## 3-qadam: Botni "uxlab qolmasligi" uchun (muhim!)
Render'ning bepul tarifi 15 daqiqa harakatsizlikdan keyin serverni
uxlatib qo'yadi. Buni oldini olish uchun:
1. https://uptimerobot.com da bepul akkaunt oching.
2. "Add New Monitor" → **HTTP(s)** turini tanlang.
3. URL sifatida Render bergan manzilni kiriting (masalan
   `https://sizning-bot.onrender.com`).
4. Har **5 daqiqada** bir marta tekshirsin deb sozlang.

Shundan keyin bot deyarli doim tayyor turadi va tekinga ishlaydi.

## Muqobil variant: o'zingizning kompyuter/serveringiz
Agar doim yoniq turadigan kompyuter yoki VPS bo'lsa, shunchaki:
```
pip install -r requirements.txt
export BOT_TOKEN="sizning_tokeningiz"
python bot.py
```
Bu holda UptimeRobot kerak emas — dastur qanchalik uzoq ishlab tursa,
bot ham shuncha ishlaydi.

## Savollarni o'zgartirish
`questions.json` faylini ochib, kerakli variant/savol/javobni tahrirlashingiz
mumkin. Format:
```json
{
  "1": {
    "questions": {
      "1": {"text": "Savol matni?", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}}
    },
    "answers": {"1": "A"}
  }
}
```
