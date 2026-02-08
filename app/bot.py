import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.logging_setup import get_logger
from app.search import get_trip, search_by_surname
from app.security import is_allowed_user, rate_limiter

router = Router()
logger = get_logger("bot")


@router.message(Command("search"))
async def handle_search(message: Message) -> None:
    user_id = str(message.from_user.id) if message.from_user else ""
    if not is_allowed_user(user_id):
        await message.answer("Доступ запрещен")
        return
    rate_key = f"tg:{user_id}"
    if not rate_limiter.allow(rate_key):
        await message.answer("Слишком много запросов, попробуи позже")
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("Нужна фамилия для поиска")
        return
    result = search_by_surname(args[1])
    if result.get("count", 0) == 0:
        await message.answer("Ничего не найдено")
        return
    for text in result.get("textMessages", []):
        await message.answer(text)


@router.message(Command("get_trip"))
async def handle_get_trip(message: Message) -> None:
    user_id = str(message.from_user.id) if message.from_user else ""
    if not is_allowed_user(user_id):
        await message.answer("Доступ запрещен")
        return
    rate_key = f"tg:{user_id}"
    if not rate_limiter.allow(rate_key):
        await message.answer("Слишком много запросов, попробуи позже")
        return
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer("Нужен идентификатор поездки")
        return
    try:
        result = get_trip(args[1])
    except LookupError:
        await message.answer("Поездка не найдена")
        return
    await message.answer(str(result))


def create_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise RuntimeError("telegram bot token missing")
    return Bot(token=settings.telegram_bot_token)


async def start_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    await dispatcher.start_polling(bot)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


async def run_bot() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    await start_polling(bot, dispatcher)


def start_bot_task(loop: asyncio.AbstractEventLoop) -> asyncio.Task:
    bot = create_bot()
    dispatcher = create_dispatcher()
    return loop.create_task(start_polling(bot, dispatcher))
