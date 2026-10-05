<p align="center">
  <img src="assets/bot-avatar.jpg" width="240" alt="ODS Berlin Bot">
</p>

# ODS Berlin Bot

On Sunday at 18:00 Europe/Berlin, [@ods_berlin_bot](https://t.me/ods_berlin_bot) posts the Wednesday data breakfast into the ODS Berlin Meetings topic. Telegram then keeps that post at the top of the topic, and the bot unpins its own post from the week before. Pins left by other people are never touched.

We use the Wednesday after that Sunday, and the `Europe/Berlin` clock keeps 18:00 through the CET and CEST switch.

## Message

The post looks like this, and the place link opens Einstein Kaffee at Alexanderplatz.

```text
☕ Дата-завтрак в среду на Alexanderplatz

В среду, 30.09, в 8:30 утра CEST
📍 Einstein Kaffee @ Alexanderplatz

Ставим 👍 кто придёт
```

## Run it

You need Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Put the bot token and the Meetings topic in `.env`, and leave that file out of git.

```text
BOT_API_TOKEN=123456:your-token
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_MESSAGE_THREAD_ID=4567
```

Add the bot to ODS Berlin and make it an admin with the Pin Messages permission. Without that permission, Telegram accepts the text and then rejects the request to keep the post at the top.

To read the two ids, start the listener and send `/ids` inside the Meetings topic. Every topic in the group returns the same chat id, but Meetings returns its own thread id.

```bash
uv run --env-file .env python announce.py --ids
```

Stop the listener after you copy the reply into `.env`.

`announce.py` refuses to post unless today is Sunday, so a manual run on another weekday can't announce the wrong week.

```bash
uv run --env-file .env python announce.py
```

Cron should call `announce.sh`, which loads `.env` and runs the command above. Schedule it for Sunday at 18:00 in the machine's local time, and keep the machine on `Europe/Berlin`.

```bash
0 18 * * SUN /path/to/ods-berlin-bot/announce.sh >> /path/to/ods-berlin-bot/logs/announce.log 2>&1
```
