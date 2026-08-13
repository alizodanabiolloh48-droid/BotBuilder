
from aiogram import Bot


async def check_bot_token(token: str):
    """
    Санҷиши token-и боти корбар.
    Агар дуруст бошад, маълумоти ботро бармегардонад.
    """

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

    except Exception:
        await bot.session.close()
        return None


async def close_bot(bot: Bot):
    """Пӯшидани connection-и bot."""
    if bot:
        await bot.session.close()
