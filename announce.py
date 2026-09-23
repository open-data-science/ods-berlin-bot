"""Post the Wednesday breakfast announcement and pin it.

Meant to run from cron on Sunday at 18:00 Europe/Berlin. The meeting is the
following Wednesday, and Europe/Berlin supplies CET or CEST across the DST change.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

BERLIN = ZoneInfo("Europe/Berlin")
MAPS_URL = "https://maps.app.goo.gl/fN63iVfjGdfFDZRBA"


def meeting_time(now: datetime) -> datetime:
    """08:30 Berlin on the Wednesday after `now`. Refuse unless today is Sunday."""
    now = now.astimezone(BERLIN)
    if now.weekday() != 6:
        raise SystemExit(
            f"Refusing to post on {now.strftime('%A %d.%m.%Y')}. "
            "Cron should run this on Sunday evening."
        )
    meeting_date = now.date() + timedelta(days=3)
    return datetime(
        meeting_date.year,
        meeting_date.month,
        meeting_date.day,
        8,
        30,
        tzinfo=BERLIN,
    )


def announcement_text(meeting: datetime) -> str:
    date_text = meeting.strftime("%d.%m")
    timezone_text = meeting.tzname()
    return (
        "☕ <b>Дата-завтрак в среду на Alexanderplatz</b>\n\n"
        f"В среду, {date_text}, в 8:30 утра {timezone_text}\n"
        f'📍 <a href="{MAPS_URL}">Einstein Kaffee @ Alexanderplatz</a>\n\n'
        "Ставим 👍 кто придёт"
    )


async def ids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the supergroup id and the forum topic the command was sent in."""
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return
    text = (
        f"chat_id: {chat.id}\n"
        f"message_thread_id: {message.message_thread_id}"
    )
    print(text, flush=True)
    await message.reply_text(text)


def listen(token: str) -> None:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("ids", ids))
    print("Listening for /ids. Send it inside the Meetings topic. Ctrl-C to stop.", flush=True)
    app.run_polling(allowed_updates=["message"])


async def post_announcement(token: str, chat_id: str, thread_id: int, text: str) -> int:
    async with Bot(token) as bot:
        message = await bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=text,
            parse_mode="HTML",
        )
        await bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message.message_id,
            disable_notification=True,
        )
    return message.message_id


def main() -> None:
    token = os.environ.get("BOT_API_TOKEN")
    if not token:
        raise SystemExit("BOT_API_TOKEN is not set")

    if "--ids" in sys.argv:
        listen(token)
        return

    try:
        meeting = meeting_time(datetime.now(BERLIN))
        text = announcement_text(meeting)
        if "--dry-run" in sys.argv:
            print(text)
            return

        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        thread_id = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID")
        if not chat_id or not thread_id:
            raise SystemExit(
                "TELEGRAM_CHAT_ID and TELEGRAM_MESSAGE_THREAD_ID are required. "
                "Run: uv run --env-file .env python announce.py --ids "
                "and send /ids inside the Meetings topic."
            )

        message_id = asyncio.run(post_announcement(token, chat_id, int(thread_id), text))
    except TelegramError as exc:
        raise SystemExit(f"Telegram API failed: {exc}") from exc

    print(
        f"posted and pinned message {message_id} "
        f"in topic {thread_id} for {meeting.strftime('%d.%m %Z')}"
    )


if __name__ == "__main__":
    main()
