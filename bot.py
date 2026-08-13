import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд!")

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
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

    keyboard.adjust(2)

    await message.answer(
        "🤖 <b>Bot Builder</b>\n\n"
        "Боти шумо барои кадом кор сохта мешавад?\n\n"
        "Як вариантро интихоб кунед:",
        reply_markup=keyboard.as_markup(),
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
async def bot_type(callback: CallbackQuery):

    names = {
        "files": "📁 Ҷустуҷӯи файлҳо",
        "media": "🖼 Акс ва дизайн",
        "shop": "🛒 Савдо",
        "video": "🎬 Видео",
        "education": "📚 Китоб / омӯзиш",
        "channel": "📢 Канал"
    }

    selected = names[callback.data]

    await callback.message.answer(
        f"✅ Шумо интихоб кардед:\n\n"
        f"<b>{selected}</b>\n\n"
        "Қадами навбатӣ:\n"
        "🔑 Токени боти худро фиристед.",
        parse_mode="HTML"
    )

    await callback.answer()


async def main():
    bot = Bot(BOT_TOKEN)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
