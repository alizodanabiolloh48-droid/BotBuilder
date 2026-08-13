import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)


async def check_bot_token(token: str):
    token = token.strip()

    if not token:
        return None

    bot = Bot(token)

    try:
        me = await bot.get_me()

        return {
            "id": me.id,
            "username": me.username,
            "name": me.full_name,
            "bot": bot,
        }

    except Exception as e:
        logging.error("Token error: %s", e)

        await bot.session.close()

        return None


async def run_user_bot(token: str, bot_type: str):
    """
    Боти шахсии корбарро иҷро мекунад.
    """

    bot = Bot(token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def user_start(message: Message):

        await message.answer(
            "🤖 Боти шумо фаъол аст!\n\n"
            f"⚙️ Навъи бот: {bot_type}\n\n"
            "🟢 Status: ONLINE"
        )

    @dp.message()
    async def user_message(message: Message):

        if bot_type == "files":

            await message.answer(
                "📁 Ҷустуҷӯи файлҳо фаъол аст.\n\n"
                "Номи файлро фиристед."
            )

        elif bot_type == "media":

            await message.answer(
                "🖼 Системаи акс ва дизайн фаъол аст."
            )

        elif bot_type == "shop":

            await message.answer(
                "🛒 Системаи савдо фаъол аст."
            )

        elif bot_type == "video":

            await message.answer(
                "🎬 Системаи видео фаъол аст."
            )

        elif bot_type == "education":

            await message.answer(
                "📚 Системаи омӯзишӣ фаъол аст."
            )

        elif bot_type == "channel":

            await message.answer(
                "📢 Системаи канал фаъол аст."
            )

        else:

            await message.answer(
                "⚙️ Боти фармоишии шумо фаъол аст."
            )

    try:

        logging.info(
            "Starting user bot: %s",
            bot_type
        )

        await dp.start_polling(bot)

    except Exception as e:

        logging.error(
            "User bot stopped: %s",
            e
        )

    finally:

        await bot.session.close()


async def close_bot(bot: Bot):

    if bot:
        await bot.session.close()
