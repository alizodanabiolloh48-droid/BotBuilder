import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import init_db, save_user
from bot_manager import check_bot_token

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд!")

dp = Dispatcher()

# Ҳолати муваққатии корбар
users = {}


# ==========================================
# МЕНЮ
# ==========================================

def main_menu():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="📁 Ҷустуҷӯи файлҳо",
        callback_data="files"
    )

    keyboard.button(
        text="🖼 Акс ва дизайн",
        callback_data="media"
    )

    keyboard.button(
        text="🛒 Савдо",
        callback_data="shop"
    )

    keyboard.button(
        text="🎬 Видео",
        callback_data="video"
    )

    keyboard.button(
        text="📚 Китоб / омӯзиш",
        callback_data="education"
    )

    keyboard.button(
        text="📢 Канал",
        callback_data="channel"
    )

    keyboard.button(
        text="⚙️ Боти дигар",
        callback_data="custom"
    )

    keyboard.adjust(2)

    return keyboard.as_markup()


# ==========================================
# START
# ==========================================

@dp.message(CommandStart())
async def start(message: Message):

    user_id = message.from_user.id

    users[user_id] = {
        "step": "type",
        "type": None,
        "token": None,
        "bot_username": None,
        "channel": None,
        "url": None
    }

    await message.answer(
        "🤖 <b>BOT BUILDER</b>\n\n"
        "Боти худро ба осонӣ созед.\n\n"
        "Боти шумо барои кадом кор сохта мешавад?",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# ==========================================
# ИНТИХОБИ НАМУДИ БОТ
# ==========================================

@dp.callback_query(
    F.data.in_({
        "files",
        "media",
        "shop",
        "video",
        "education",
        "channel",
        "custom"
    })
)
async def select_type(callback: CallbackQuery):

    user_id = callback.from_user.id

    if user_id not in users:
        users[user_id] = {}

    names = {
        "files": "📁 Ҷустуҷӯи файлҳо",
        "media": "🖼 Акс ва дизайн",
        "shop": "🛒 Савдо",
        "video": "🎬 Видео",
        "education": "📚 Китоб / омӯзиш",
        "channel": "📢 Канал",
        "custom": "⚙️ Боти дигар"
    }

    users[user_id]["type"] = callback.data
    users[user_id]["step"] = "token"

    await callback.message.answer(
        f"✅ <b>{names[callback.data]}</b>\n\n"
        "🔑 Токени боти худро фиристед.\n\n"
        "Token аз @BotFather гирифта мешавад.",
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
# ҚАБУЛИ TOKEN / CHANNEL / URL
# ==========================================

@dp.message()
async def process_message(message: Message):

    user_id = message.from_user.id

    if user_id not in users:
        await message.answer(
            "Аввал /start-ро пахш кунед."
        )
        return

    data = users[user_id]
    step = data.get("step")

    if not message.text:
        await message.answer(
            "❌ Лутфан маълумотро ҳамчун матн фиристед."
        )
        return

    text = message.text.strip()

    # ======================================
    # TOKEN
    # ======================================

    if step == "token":

        await message.answer(
            "🔄 Token санҷида мешавад..."
        )

        result = await check_bot_token(text)

        if not result:

            await message.answer(
                "❌ <b>Token нодуруст аст.</b>\n\n"
                "Token-ро аз @BotFather санҷед ва дубора фиристед.",
                parse_mode="HTML"
            )

            return

        data["token"] = text
        data["bot_username"] = result["username"]
        data["step"] = "channel"

        # connection-ро мепӯшем
        await result["bot"].session.close()

        await message.answer(
            "✅ <b>Token дуруст аст!</b>\n\n"
            f"🤖 Бот: @{result['username']}\n"
            f"👤 Ном: {result['name']}\n\n"
            "📢 Акнун @username-и канали худро фиристед.\n\n"
            "Мисол:\n"
            "<code>@mychannel</code>",
            parse_mode="HTML"
        )

        return

    # ======================================
    # CHANNEL
    # ======================================

    if step == "channel":

        if not text.startswith("@"):

            await message.answer(
                "❌ Формати канал нодуруст аст.\n\n"
                "Мисол:\n"
                "<code>@mychannel</code>",
                parse_mode="HTML"
            )

            return

        data["channel"] = text
        data["step"] = "url"

        await message.answer(
            "✅ Канал қабул шуд.\n\n"
            "🔗 Акнун URL-и каналро фиристед.\n\n"
            "Мисол:\n"
            "<code>https://t.me/mychannel</code>",
            parse_mode="HTML"
        )

        return

    # ======================================
    # URL
    # ======================================

    if step == "url":

        if not (
            text.startswith("https://t.me/")
            or text.startswith("http://t.me/")
        ):

            await message.answer(
                "❌ URL нодуруст аст.\n\n"
                "Мисол:\n"
                "<code>https://t.me/mychannel</code>",
                parse_mode="HTML"
            )

            return

        data["url"] = text
        data["step"] = "ready"

        # Сабт дар база
        save_user(
            user_id=user_id,
            bot_type=data["type"],
            bot_token=data["token"],
            bot_username=data["bot_username"],
            channel=data["channel"],
            channel_url=data["url"],
            status="ready"
        )

        keyboard = InlineKeyboardBuilder()

        keyboard.button(
            text="🚀 Ба кор даровардани бот",
            callback_data="launch_bot"
        )

        keyboard.button(
            text="🔄 Аз нав оғоз кардан",
            callback_data="restart_setup"
        )

        keyboard.adjust(1)

        await message.answer(
            "🎉 <b>Тамом!</b>\n\n"
            f"🤖 Бот: @{data['bot_username']}\n"
            f"📢 Канал: {data['channel']}\n"
            f"🔗 URL: {data['url']}\n\n"
            "Ҳамаи маълумот қабул шуд.\n"
            "Акнун метавонед ботро ба кор дароред.",
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

        return

    await message.answer(
        "Барои оғоз /start-ро пахш кунед."
    )


# ==========================================
# LAUNCH
# ==========================================

@dp.callback_query(F.data == "launch_bot")
async def launch_bot(callback: CallbackQuery):

    user_id = callback.from_user.id

    if user_id not in users:

        await callback.answer(
            "Маълумот ёфт нашуд.",
            show_alert=True
        )

        return

    data = users[user_id]

    if data.get("step") != "ready":

        await callback.answer(
            "Аввал ҳамаи маълумотро пур кунед.",
            show_alert=True
        )

        return

    await callback.message.answer(
        "⚙️ <b>Бот омода мешавад...</b>\n\n"
        "🔹 Санҷиши конфигурация...\n"
        "🔹 Омода кардани функсияҳо...\n"
        "🔹 Пайвастшавӣ ба Telegram...",
        parse_mode="HTML"
    )

    # Ҳоло танҳо статусро active мекунем.
    # Worker-и воқеии multi-bot дар қадами баъдӣ илова мешавад.

    save_user(
        user_id=user_id,
        bot_type=data["type"],
        bot_token=data["token"],
        bot_username=data["bot_username"],
        channel=data["channel"],
        channel_url=data["url"],
        status="active"
    )

    data["step"] = "active"

    await callback.message.answer(
        "🟢 <b>Боти шумо фаъол шуд!</b>\n\n"
        f"🤖 @{data['bot_username']}\n"
        f"📢 {data['channel']}\n\n"
        "⚙️ Вазифа:\n"
        f"<b>{data['type']}</b>",
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
# RESTART
# ==========================================

@dp.callback_query(F.data == "restart_setup")
async def restart_setup(callback: CallbackQuery):

    user_id = callback.from_user.id

    users[user_id] = {
        "step": "type",
        "type": None,
        "token": None,
        "bot_username": None,
        "channel": None,
        "url": None
    }

    await callback.message.answer(
        "🔄 Боз оғоз мекунем.\n\n"
        "Боти шумо барои кадом кор сохта мешавад?",
        reply_markup=main_menu()
    )

    await callback.answer()


# ==========================================
# MAIN
# ==========================================

async def main():

    init_db()

    bot = Bot(BOT_TOKEN)

    try:

        await dp.start_polling(bot)

    finally:

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
