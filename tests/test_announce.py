from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo
import pytest
from telegram.error import TelegramError

from announce import (
    BERLIN,
    announcement_text,
    last_bot_pin,
    meeting_time,
    post_announcement,
    unpin_previous,
)


def test_meeting_time_sunday():
    sunday = datetime(2026, 10, 11, 18, 0, tzinfo=BERLIN)
    meeting = meeting_time(sunday)
    assert meeting == datetime(2026, 10, 14, 8, 30, tzinfo=BERLIN)
    assert meeting.tzname() == "CEST"


def test_meeting_time_non_sunday_refuses():
    monday = datetime(2026, 10, 12, 10, 0, tzinfo=BERLIN)
    with pytest.raises(SystemExit) as exc:
        meeting_time(monday)
    assert "Refusing to post on Monday" in str(exc.value)


def test_meeting_time_dry_run_allows_non_sunday():
    monday = datetime(2026, 10, 12, 10, 0, tzinfo=BERLIN)
    meeting = meeting_time(monday, dry_run=True)
    assert meeting == datetime(2026, 10, 14, 8, 30, tzinfo=BERLIN)

    wednesday = datetime(2026, 10, 14, 12, 0, tzinfo=BERLIN)
    next_meeting = meeting_time(wednesday, dry_run=True)
    assert next_meeting == datetime(2026, 10, 21, 8, 30, tzinfo=BERLIN)


def test_announcement_text():
    meeting = datetime(2026, 10, 14, 8, 30, tzinfo=BERLIN)
    text = announcement_text(meeting)
    assert "14.10" in text
    assert "CEST" in text
    assert "https://maps.app.goo.gl/fN63iVfjGdfFDZRBA" in text
    assert "☕ <b>Дата-завтрак в среду на Alexanderplatz</b>" in text


@pytest.mark.asyncio
async def test_last_bot_pin_no_pin():
    bot = MagicMock()
    bot.id = 123
    chat = MagicMock()
    chat.pinned_message = None
    bot.get_chat = AsyncMock(return_value=chat)

    assert await last_bot_pin(bot, "-100123") is None


@pytest.mark.asyncio
async def test_last_bot_pin_pin_from_other_user():
    bot = MagicMock()
    bot.id = 123
    chat = MagicMock()
    pinned = MagicMock()
    pinned.message_id = 999
    pinned.from_user = MagicMock(id=456)
    chat.pinned_message = pinned
    bot.get_chat = AsyncMock(return_value=chat)

    assert await last_bot_pin(bot, "-100123") is None


@pytest.mark.asyncio
async def test_last_bot_pin_pin_from_bot():
    bot = MagicMock()
    bot.id = 123
    chat = MagicMock()
    pinned = MagicMock()
    pinned.message_id = 888
    pinned.from_user = MagicMock(id=123)
    chat.pinned_message = pinned
    bot.get_chat = AsyncMock(return_value=chat)

    assert await last_bot_pin(bot, "-100123") == 888


@pytest.mark.asyncio
async def test_last_bot_pin_telegram_error_handled():
    bot = MagicMock()
    bot.id = 123
    bot.get_chat = AsyncMock(side_effect=TelegramError("Network failed"))

    assert await last_bot_pin(bot, "-100123") is None


@pytest.mark.asyncio
async def test_unpin_previous():
    bot = MagicMock()
    bot.unpin_chat_message = AsyncMock()

    # None stale_id
    await unpin_previous(bot, "-100123", None, 100)
    bot.unpin_chat_message.assert_not_called()

    # stale_id equals new_id
    await unpin_previous(bot, "-100123", 100, 100)
    bot.unpin_chat_message.assert_not_called()

    # unpins stale_id
    await unpin_previous(bot, "-100123", 99, 100)
    bot.unpin_chat_message.assert_awaited_once_with(chat_id="-100123", message_id=99)

    # handles TelegramError gracefully
    bot.unpin_chat_message = AsyncMock(side_effect=TelegramError("Cannot unpin"))
    await unpin_previous(bot, "-100123", 98, 100)


@pytest.mark.asyncio
async def test_post_announcement():
    mock_bot = MagicMock()
    mock_bot.id = 123
    mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
    mock_bot.__aexit__ = AsyncMock(return_value=None)

    mock_chat = MagicMock()
    mock_chat.pinned_message = None
    mock_bot.get_chat = AsyncMock(return_value=mock_chat)

    mock_sent_msg = MagicMock()
    mock_sent_msg.message_id = 42
    mock_bot.send_message = AsyncMock(return_value=mock_sent_msg)
    mock_bot.pin_chat_message = AsyncMock()
    mock_bot.unpin_chat_message = AsyncMock()

    with patch("announce.Bot", return_value=mock_bot):
        res = await post_announcement("fake-token", "-100123", 547, "test message")
        assert res == 42
        mock_bot.send_message.assert_awaited_once_with(
            chat_id="-100123",
            message_thread_id=547,
            text="test message",
            parse_mode="HTML",
        )
        mock_bot.pin_chat_message.assert_awaited_once_with(
            chat_id="-100123",
            message_id=42,
            disable_notification=True,
        )

