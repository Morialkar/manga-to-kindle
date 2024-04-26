from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Optional

import httpx
from aws_lambda_typing import context as context_
from aws_lambda_typing import events, responses
from telegram import Message, Update, User
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)
from typing_extensions import TypeGuard

from op_downloader.downloader import ChaptersDownloader
from op_downloader.exceptions import ChapterNotFoundError

# Logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# Asyncio event loop
LOOP = asyncio.new_event_loop()

# Telegram application context
APPLICATION = None

# Downloaded chapters directory so they can be re-used
CHAPTERS_OUT_PATH = Path("/tmp")

# Easter egg of character after downloading a chapter
CHARACTERS = (
    "🍖🍖😁🍖🍖",
    "🍺⚔😏⚔🍺",
    "🍊💰😜💰🌩",
    "💃🍚😍🍽👯",
    "🎯🌱😱🌱🎯",
    "💉💊🐐💊💉",
    "📚🗿💁🏻🗿📚",
    "🔩🛠🤖🚤⚙",
    "🎼🎹💀🎻🗡",
)

HELP_MSG = """
❓❓❓

  • `/start`: Get a warm welcome message\!
  • `/help`: Sends this message
  • `/download \<chapter number\>`: Download a one piece manga chapter

All the chapters I provide are downloaded from [TCB Scans](https://tcbscans.carrd.co/)\.
So shotout to them\!
"""


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not _has_message_and_user(update):
        raise ValueError("invalid update")

    msg = "\n".join([
        f"👋🏼👋🏼👋🏼 Hi {update.effective_user.mention_markdown_v2()}\!",
        "Welcome to One Piece Manga Bot Downloader\!",
        "Read the below instructions to learn how to download a chapter\.",
        "Let's set sail for the Grand Line\!",
    ])
    await update.message.reply_markdown_v2(msg)
    await update.message.reply_markdown_v2(HELP_MSG)


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if not _has_message_and_user(update):
        raise ValueError("invalid update")

    await update.message.reply_markdown_v2(HELP_MSG)


async def download_command(update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _has_message_and_user(update):
        raise ValueError("invalid update")

    LOGGER.debug(
        f"Download chapter command issued. Chapter text: {update.message.text}"
    )
    chapter_txt = update.message.text.removeprefix("/download ").strip()
    try:
        chapter = int(chapter_txt)
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid chapter number: {chapter_txt}...")
        return

    character = random.choice(CHARACTERS)  # Easter egg random character

    async with httpx.AsyncClient(follow_redirects=True) as client:
        cd = ChaptersDownloader(client, chapters_output_path=CHAPTERS_OUT_PATH)
        await update.message.reply_text(
            f"⏳ Downloading chapter {chapter}, please wait...")
        try:
            [chapter_path] = await cd.run([chapter])
        except ChapterNotFoundError as err:
            await update.message.reply_text(
                f"❌ Chapter {err.chapter} is not yet avaialble.")
            return

    await update.message.reply_document(
        str(chapter_path),
        caption=f"{character} Here you have your chapter, enjoy it!")


async def no_valid_message(update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    if not _has_message_and_user(update):
        raise ValueError("invalid update")

    await update.message.reply_text(
        "❌ I can't help you, seems you sent an invalid command...")


async def unexpected_error_handler(update: Optional[Update],
                                   context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🐛 Unexpected error found..."
                                    )  # type: ignore
    await update.message.reply_text(  # type: ignore
        context.error.with_traceback(),  # type: ignore
    )


async def setup_application() -> Application:
    global APPLICATION
    if APPLICATION is None:
        APPLICATION = Application.builder().token(
            os.environ["BOT_TOKEN"]).build()

        # Command handlers
        APPLICATION.add_handler(CommandHandler("start", start))
        APPLICATION.add_handler(CommandHandler("help", help_command))
        APPLICATION.add_handler(CommandHandler("download", download_command))

        # Error handler
        APPLICATION.add_error_handler(unexpected_error_handler)  # type: ignore

        # Fallback invalid command
        APPLICATION.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, no_valid_message))

        await APPLICATION.initialize()

    return APPLICATION


def main(event: events.APIGatewayProxyEventV2,
         ctx: context_.Context) -> responses.APIGatewayProxyResponseV2:
    # Parse HTTP request body
    body = json.loads(event["body"])
    LOGGER.debug(f"Request body: {body}")

    # Initialize Telegram application
    app = LOOP.run_until_complete(setup_application())

    # Process the request
    update = Update.de_json(body, app.bot)
    LOOP.run_until_complete(app.process_update(update))

    return {"statusCode": 200}


# Typing utilities
class _TextMessage(Message):
    text: str


class _UpdateRequiredMessage(Update):
    message: _TextMessage
    effective_user: User


def _has_message_and_user(update: Update) -> TypeGuard[_UpdateRequiredMessage]:
    return bool(update.message and update.effective_user)
