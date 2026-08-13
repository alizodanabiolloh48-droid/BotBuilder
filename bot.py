import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramUnauthorizedError

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд!")

dp = Dispatcher()

# Ҳолати муваққатии корбарон
users = {}


def main_menu():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text="📁 Файлҳо", callback_data="files")
    keyboard.button(text="🖼 Акс / дизайн", callback_data="media")
    keyboard.button(text="🛒 Савдо", callback_data="shop")
    keyboard.button(text="🎬 Видео", callback_data="video")
    keyboard.button(text="📚 Китоб", callback_data="education")
    keyboard.button(text="📢 Канал", callback_data="channel")

    keyboard.adjust(2)
    return keyboard.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    users[message.from_user.id] = {
        "step": "type",
        "type": None,
        "token": None,
        "channel": None,
        "url": None,
    }

    await message.answer(
        "🤖 <b>Bot Builder</b>\n\n"
        "Боти шумо барои кадом кор сохта мешавад?\n\n"
        "Яке аз вариантҳоро интихоб кунед:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.in_({
    "files",
    "media",
    "shop",
    "video",
    "education",
    "channel"
}))
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
    }

    users[user_id]["type"] = callback.data
    users[user_id]["step"] = "token"

    await callback.message.answer(
        f"✅ Интихоб шуд: <b>{names[callback.data]}</b>\n\n"
        "🔑 Ҳоло токени боти худро фиристед.\n\n"
        "⚠️ Token танҳо дар дохили система коркард мешавад.",
        parse_mode="HTML"
    )

    await callback.answer()


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

    # ==========================
    # TOKEN
    # ==========================

    if step == "token":

        token = message.text.strip()

        await message.answer(
            "🔄 Token санҷида мешавад..."
        )

        try:
            test_bot = Bot(token)

            me = await test_bot.get_me()

            await test_bot.session.close()

            data["token"] = token
            data["step"] = "channel"

            await message.answer(
                "✅ <b>Token дуруст аст!</b>\n\n"
                f"🤖 Номи бот: <b>{me.full_name}</b>\n"
                f"🔹 Username: @{me.username}\n\n"
                "📢 Акнун @username-и канали худро фиристед.",
                parse_mode="HTML"
            )

        except TelegramUnauthorizedError:

            await message.answer(
                "❌ Token нодуруст аст.\n\n"
                "Token-ро аз BotFather санҷед ва дубора фиристед."
            )

        except Exception as e:

            logging.error("Token error: %s", e)

            await message.answer(
                "❌ Token санҷида нашуд.\n"
                "Дубора кӯшиш кунед."
            )

        return

    # ==========================
    # CHANNEL
    # ==========================

    if step == "channel":

        channel = message.text.strip()

        if not channel.startswith("@"):
            await message.answer(
                "❌ Формат нодуруст аст.\n\n"
                "Мисол:\n"
                "@mychannel"
            )
            return

        data["channel"] = channel
        data["step"] = "url"

        await message.answer(
            "✅ Канал қабул шуд.\n\n"
            "🔗 Акнун силкаи канали худро фиристед.\n\n"
            "Мисол:\n"
            "https://t.me/mychannel"
        )

        return

    # ==========================
    # URL
    # ==========================

    if step == "url":

        url = message.text.strip()

        if not (
            url.startswith("https://t.me/")
            or url.startswith("http://t.me/")
        ):
            await message.answer(
                "❌ URL нодуруст аст.\n\n"
                "Мисол:\n"
                "https://t.me/mychannel"
            )
            return

        data["url"] = url
        data["step"] = "ready"

        await message.answer(
            "🎉 <b>Ҳамаи маълумот қабул шуд!</b>\n\n"
            f"🤖 Навъи бот: <code>{data['type']}</code>\n"
            f"📢 Канал: <code>{data['channel']}</code>\n"
            f"🔗 URL: {data['url']}\n\n"
            "⚙️ Қадами навбатӣ: сохтани конфигурация ва фаъол кардани боти шахсӣ.",
            parse_mode="HTML"
        )

        return


async def main():

    bot = Bot(BOT_TOKEN)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
