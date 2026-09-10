import asyncio
import json
import logging
import os
import random
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# SOZLAMALAR
# -----------------------------------------------------------------------
# Tokenni bevosita shu yerga yozmang! Server muhitida "BOT_TOKEN" nomli
# environment variable orqali beriladi (Render/Railway paneliga qo'shiladi).
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ_SHU_YERGA")
PORT = int(os.environ.get("PORT", 10000))

with open(os.path.join(os.path.dirname(__file__), "questions.json"), encoding="utf-8") as f:
    VARIANTS = json.load(f)  # {"1": {"questions": {...}, "answers": {...}}, ...}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Har bir foydalanuvchining joriy holati shu yerda saqlanadi (xotirada).
# user_id -> {"variant": str, "order": [qnum,...], "idx": int, "correct": int}
sessions: dict[int, dict] = {}


def variants_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for vnum in sorted(VARIANTS.keys(), key=int):
        row.append(InlineKeyboardButton(text=f"{vnum}-variant", callback_data=f"start_variant:{vnum}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def question_keyboard(qnum: int, options: dict) -> InlineKeyboardMarkup:
    # Tugmalarda faqat harf ko'rsatiladi — javob matni savol ichida to'liq beriladi.
    # Telegram tugma matnini cheklaganidan uzun javoblar kesilib qolmasligi uchun shunday qilingan.
    row = []
    for letter in ["A", "B", "C", "D"]:
        if letter in options:
            row.append(InlineKeyboardButton(text=letter, callback_data=f"answer:{qnum}:{letter}"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def format_options(options: dict) -> str:
    lines = []
    for letter in ["A", "B", "C", "D"]:
        if letter in options:
            lines.append(f"{letter}) {options[letter]}")
    return "\n".join(lines)


async def send_question(chat_id: int, user_id: int):
    session = sessions[user_id]
    idx = session["idx"]
    order = session["order"]

    if idx >= len(order):
        await finish_quiz(chat_id, user_id)
        return

    qnum = order[idx]
    variant = VARIANTS[session["variant"]]
    q = variant["questions"][str(qnum)]

    text = f"❓ Savol {idx + 1}/{len(order)}\n\n{q['text']}\n\n{format_options(q['options'])}"
    await bot.send_message(chat_id, text, reply_markup=question_keyboard(qnum, q["options"]))


async def finish_quiz(chat_id: int, user_id: int):
    session = sessions.pop(user_id, None)
    if session is None:
        return
    total = len(session["order"])
    correct = session["correct"]
    percent = round(correct / total * 100, 1) if total else 0

    text = (
        f"✅ Test yakunlandi!\n\n"
        f"Variant: {session['variant']}\n"
        f"To'g'ri javoblar: {correct}/{total}\n"
        f"Natija: {percent}%"
    )
    await bot.send_message(chat_id, text, reply_markup=variants_keyboard())


@dp.message(CommandStart())
async def cmd_start(message: Message):
    sessions.pop(message.from_user.id, None)
    await message.answer(
        "Assalomu alaykum! Test botiga xush kelibsiz.\n\n"
        "Quyidagi variantlardan birini tanlang:",
        reply_markup=variants_keyboard(),
    )


@dp.callback_query(F.data.startswith("start_variant:"))
async def cb_start_variant(callback: CallbackQuery):
    vnum = callback.data.split(":")[1]
    variant = VARIANTS[vnum]
    qnums = [int(x) for x in variant["questions"].keys()]
    random.shuffle(qnums)  # savollar tartibi har safar aralashtiriladi

    sessions[callback.from_user.id] = {
        "variant": vnum,
        "order": qnums,
        "idx": 0,
        "correct": 0,
    }

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(f"{vnum}-variant boshlandi!")
    await send_question(callback.message.chat.id, callback.from_user.id)


@dp.callback_query(F.data.startswith("answer:"))
async def cb_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = sessions.get(user_id)
    if session is None:
        await callback.answer("Iltimos, /start bosib qaytadan boshlang.", show_alert=True)
        return

    _, qnum_str, letter = callback.data.split(":")
    qnum = int(qnum_str)

    # Bu savol allaqachon javob berilganmi (eski xabar tugmasi bosilsa)
    idx = session["idx"]
    if idx >= len(session["order"]) or session["order"][idx] != qnum:
        await callback.answer("Bu savol allaqachon o'tildi.", show_alert=True)
        return

    variant = VARIANTS[session["variant"]]
    correct_letter = variant["answers"][str(qnum)]
    options = variant["questions"][str(qnum)]["options"]
    is_correct = letter == correct_letter

    if is_correct:
        session["correct"] += 1
        feedback = f"🟢 To'g'ri javob: {letter}) {options[letter]}"
    else:
        feedback = (
            f"🔴 Sizning javobingiz: {letter}) {options[letter]}\n"
            f"🟢 To'g'ri javob: {correct_letter}) {options[correct_letter]}"
        )

    await callback.answer("To'g'ri!" if is_correct else "Noto'g'ri", show_alert=False)
    # Savol matnini saqlab qolamiz, faqat tugmalarni olib tashlaymiz va natijani pastiga qo'shamiz.
    new_text = f"{callback.message.text}\n\n{feedback}"
    await callback.message.edit_text(new_text, reply_markup=None)

    session["idx"] += 1
    await send_question(callback.message.chat.id, user_id)


# -----------------------------------------------------------------------
# Render/Railway kabi bepul hostinglar doim HTTP portini tinglashni talab
# qiladi. Shu sabab botni polling rejimida ishga tushiramiz, lekin yonida
# UptimeRobot kabi xizmatlar "uxlab qolmasin" deb ping qilib turishi uchun
# mayda health-check server ham ko'taramiz.
# -----------------------------------------------------------------------
async def health(request):
    return web.Response(text="Bot ishlayapti ✅")


async def run_web_app():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health-check server {PORT}-portda ishga tushdi")


async def main():
    await run_web_app()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
