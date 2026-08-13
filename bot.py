import asyncio
import logging
import os
import re
from contextlib import suppress

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

BOT_BUILDER_TOKEN = os.getenv("BOT_BUILDER_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_BUILDER_TOKEN:
    raise RuntimeError(
        "BOT_BUILDER_TOKEN ёфт нашуд!"
    )

if not WEBHOOK_URL:
    raise RuntimeError(
        "WEBHOOK_URL ёфт нашуд!"
    )


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger("bot-builder")


database.init_db()


# =========================================================
# MAIN BOT
# =========================================================

main_bot = Bot(BOT_BUILDER_TOKEN)
main_dp = Dispatcher()

app = FastAPI(
    title="Telegram Bot Builder"
)


# =========================================================
# STATES
# =========================================================

class CreateBot(StatesGroup):
    category = State()
    token = State()
    channel = State()
    channel_url = State()


class SearchFile(StatesGroup):
    query = State()


# =========================================================
# KEYBOARDS
# =========================================================

def category_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼 Аксҳо",
                    callback_data="category:photos"
                ),
                InlineKeyboardButton(
                    text="🎬 Видео",
                    callback_data="category:videos"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📁 Файлҳо",
                    callback_data="category:files"
                ),
                InlineKeyboardButton(
                    text="🔎 Ҷустуҷӯ",
                    callback_data="category:search"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛍 Савдо",
                    callback_data="category:shop"
                ),
                InlineKeyboardButton(
                    text="📢 Канал",
                    callback_data="category:channel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Дигар",
                    callback_data="category:other"
                )
            ]
        ]
    )


# =========================================================
# START
# =========================================================

@main_dp.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    database.add_user(
        message.from_user.id
    )

    await message.answer(
        "👋 Салом!\n\n"
        "🤖 Ман Bot Builder ҳастам.\n\n"
        "Боти худро барои кадом кор месозед?",
        reply_markup=category_keyboard()
    )


# =========================================================
# CATEGORY
# =========================================================

@main_dp.callback_query(
    F.data.startswith("category:")
)
async def category_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    category = callback.data.split(":", 1)[1]

    await state.update_data(
        category=category
    )

    await state.set_state(
        CreateBot.token
    )

    await callback.message.edit_text(
        "🔑 Bot Token-ро фиристед.\n\n"
        "Token бояд аз @BotFather гирифта шуда бошад."
    )

    await callback.answer()


# =========================================================
# TOKEN
# =========================================================

@main_dp.message(CreateBot.token)
async def token_handler(
    message: Message,
    state: FSMContext
):

    token = message.text.strip()

    if not re.match(
        r"^\d{6,15}:[A-Za-z0-9_-]{20,}$",
        token
    ):
        await message.answer(
            "❌ Token нодуруст аст."
        )
        return

    test_bot = Bot(token)

    try:

        info = await test_bot.get_me()

    except Exception:

        await message.answer(
            "❌ Token кор намекунад."
        )

        return

    finally:

        with suppress(Exception):
            await test_bot.session.close()

    await state.update_data(
        token=token,
        bot_id=info.id,
        bot_username=info.username or "",
        bot_name=info.first_name or ""
    )

    await state.set_state(
        CreateBot.channel
    )

    await message.answer(
        f"✅ Token дуруст аст.\n\n"
        f"🤖 @{info.username}\n\n"
        "📢 @username-и канали худро фиристед."
    )


# =========================================================
# CHANNEL
# =========================================================

@main_dp.message(CreateBot.channel)
async def channel_handler(
    message: Message,
    state: FSMContext
):

    channel = message.text.strip()

    if not re.match(
        r"^@[A-Za-z0-9_]{5,}$",
        channel
    ):
        await message.answer(
            "❌ Масалан: @my_channel"
        )
        return

    data = await state.get_data()

    test_bot = Bot(
        data["token"]
    )

    try:

        chat = await test_bot.get_chat(
            channel
        )

        if chat.type != "channel":
            await message.answer(
                "❌ Ин Channel нест."
            )
            return

        member = await test_bot.get_chat_member(
            chat.id,
            data["bot_id"]
        )

        if member.status not in (
            "administrator",
            "creator"
        ):
            await message.answer(
                "❌ Аввал ботро ба канал "
                "ҳамчун Administrator илова кунед."
            )
            return

    except Exception:

        await message.answer(
            "❌ Канал ёфт нашуд."
        )

        return

    finally:

        with suppress(Exception):
            await test_bot.session.close()

    await state.update_data(
        channel=channel
    )

    await state.set_state(
        CreateBot.channel_url
    )

    await message.answer(
        "🔗 URL-и каналро фиристед.\n\n"
        "Мисол:\n"
        "https://t.me/my_channel"
    )


# =========================================================
# CHANNEL URL
# =========================================================

@main_dp.message(CreateBot.channel_url)
async def channel_url_handler(
    message: Message,
    state: FSMContext
):

    url = message.text.strip()

    if not re.match(
        r"^https://t\.me/[A-Za-z0-9_+/-]+$",
        url
    ):
        await message.answer(
            "❌ URL нодуруст аст."
        )
        return

    data = await state.get_data()

    database.save_bot(
        owner_id=message.from_user.id,
        bot_id=data["bot_id"],
        bot_username=data["bot_username"],
        bot_name=data["bot_name"],
        token=data["token"],
        category=data["category"],
        channel_username=data["channel"],
        channel_url=url
    )

    await state.clear()

    await message.answer(
        "🎉 Боти шумо сохта шуд!\n\n"
        f"🤖 @{data['bot_username']}\n"
        f"📢 {data['channel']}\n\n"
        "Ҳоло webhook-и бот насб мешавад."
    )

    await setup_child_bot(
        data["bot_id"]
    )


# =========================================================
# CHILD BOT ROUTER
# =========================================================

def create_child_router(bot_id):

    router = Router()

    @router.message(CommandStart())
    async def child_start(
        message: Message
    ):

        await message.answer(
            "👋 Салом!\n\n"
            "🔎 Номи файлро нависед.\n"
            "Ман аз база ҷустуҷӯ мекунам."
        )


    @router.message(F.document)
    async def document_handler(
        message: Message
    ):

        document = message.document

        name = (
            document.file_name
            or f"file_{message.message_id}"
        )

        database.add_file(
            bot_id=bot_id,
            file_name=name,
            file_id=document.file_id,
            file_type="document",
            message_id=message.message_id
        )

        await message.answer(
            f"✅ Файл нигоҳ дошта шуд:\n{name}"
        )


    @router.message(F.photo)
    async def photo_handler(
        message: Message
    ):

        photo = message.photo[-1]

        name = (
            message.caption
            or f"photo_{message.message_id}.jpg"
        )

        database.add_file(
            bot_id=bot_id,
            file_name=name,
            file_id=photo.file_id,
            file_type="photo",
            message_id=message.message_id
        )

        await message.answer(
            "🖼 Акс нигоҳ дошта шуд."
        )


    @router.message(F.video)
    async def video_handler(
        message: Message
    ):

        video = message.video

        name = (
            video.file_name
            or message.caption
            or f"video_{message.message_id}.mp4"
        )

        database.add_file(
            bot_id=bot_id,
            file_name=name,
            file_id=video.file_id,
            file_type="video",
            message_id=message.message_id
        )

        await message.answer(
            "🎬 Видео нигоҳ дошта шуд."
        )


    @router.message(F.text)
    async def search_handler(
        message: Message
    ):

        query = message.text.strip()

        if not query:
            return

        results = database.search_files(
            bot_id,
            query
        )

        if not results:

            await message.answer(
                f"❌ Барои «{query}» чизе ёфт нашуд."
            )

            return

        await message.answer(
            f"🔎 Натиҷаҳо: {len(results)}"
        )

        for item in results:

            try:

                if item["file_type"] == "photo":

                    await message.answer_photo(
                        item["file_id"],
                        caption=item["file_name"]
                    )

                elif item["file_type"] == "video":

                    await message.answer_video(
                        item["file_id"],
                        caption=item["file_name"]
                    )

                else:

                    await message.answer_document(
                        item["file_id"],
                        caption=item["file_name"]
                    )

            except Exception as e:

                logger.error(
                    "Send file error: %s",
                    e
                )


    return router


# =========================================================
# CHILD BOT WEBHOOK
# =========================================================

child_dispatchers = {}
child_bots = {}


async def setup_child_bot(bot_id):

    item = database.get_bot(
        bot_id
    )

    if not item:
        return

    token = database.decrypt_token(
        item["token_encrypted"]
    )

    bot = Bot(token)

    dp = Dispatcher()

    dp.include_router(
        create_child_router(bot_id)
    )

    child_bots[bot_id] = bot
    child_dispatchers[bot_id] = dp

    webhook = (
        f"{WEBHOOK_URL.rstrip('/')}"
        f"/telegram/{bot_id}"
    )

    await bot.set_webhook(
        webhook,
        drop_pending_updates=True
    )

    logger.info(
        "Webhook enabled: %s",
        webhook
    )


# =========================================================
# MAIN WEBHOOK
# =========================================================

@app.post("/telegram/main")
async def main_webhook(
    request: Request
):

    data = await request.json()

    update = Update.model_validate(
        data
    )

    await main_dp.feed_update(
        main_bot,
        update
    )

    return JSONResponse(
        {"ok": True}
    )


# =========================================================
# CHILD WEBHOOK
# =========================================================

@app.post("/telegram/{bot_id}")
async def child_webhook(
    bot_id: int,
    request: Request
):

    dp = child_dispatchers.get(
        bot_id
    )

    bot = child_bots.get(
        bot_id
    )

    if not dp or not bot:

        return JSONResponse(
            {
                "ok": False,
                "error": "bot_not_loaded"
            },
            status_code=404
        )

    data = await request.json()

    update = Update.model_validate(
        data
    )

    await dp.feed_update(
        bot,
        update
    )

    return JSONResponse(
        {"ok": True}
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
async def home():

    return {
        "status": "online",
        "service": "Telegram Bot Builder"
    }


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup():

    await main_bot.set_webhook(
        f"{WEBHOOK_URL.rstrip('/')}/telegram/main",
        drop_pending_updates=True
    )

    active = database.get_active_bots()

    for item in active:

        try:

            await setup_child_bot(
                item["bot_id"]
            )

        except Exception as e:

            logger.exception(
                "Failed to start bot %s: %s",
                item["bot_id"],
                e
            )


# =========================================================
# SHUTDOWN
# =========================================================

@app.on_event("shutdown")
async def shutdown():

    with suppress(Exception):
        await main_bot.delete_webhook()

    for bot in child_bots.values():

        with suppress(Exception):
            await bot.delete_webhook()

        with suppress(Exception):
            await bot.session.close()

    with suppress(Exception):
        await main_bot.session.close()
