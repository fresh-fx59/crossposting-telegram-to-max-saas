import io
import logging
import os

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MAX_BOT_TOKEN = os.environ["MAX_BOT_TOKEN"]
MAX_CHAT_ID = int(os.environ["MAX_CHAT_ID"])

MAX_API_BASE = "https://platform-api.max.ru"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def send_max_text(client: httpx.AsyncClient, text: str) -> None:
    """Send a text message to Max chat."""
    resp = await client.post(
        f"{MAX_API_BASE}/messages",
        params={"access_token": MAX_BOT_TOKEN, "chat_id": MAX_CHAT_ID},
        json={"text": text},
    )
    resp.raise_for_status()
    logger.info("Sent text to Max: %s", resp.json())


async def upload_max_photo(
    client: httpx.AsyncClient, photo_bytes: bytes, filename: str
) -> dict:
    """Upload a photo to Max and return the upload response."""
    resp = await client.post(
        f"{MAX_API_BASE}/uploads",
        params={
            "access_token": MAX_BOT_TOKEN,
            "chat_id": MAX_CHAT_ID,
            "type": "photo",
        },
        content=photo_bytes,
        headers={"Content-Type": "image/jpeg"},
    )
    resp.raise_for_status()
    return resp.json()


async def send_max_photo(
    client: httpx.AsyncClient,
    upload_result: dict,
    caption: str | None = None,
) -> None:
    """Send a message with an uploaded photo attachment to Max."""
    body: dict = {
        "attachments": [
            {
                "type": "image",
                "payload": upload_result,
            }
        ],
    }
    if caption:
        body["text"] = caption

    resp = await client.post(
        f"{MAX_API_BASE}/messages",
        params={"access_token": MAX_BOT_TOKEN, "chat_id": MAX_CHAT_ID},
        json=body,
    )
    resp.raise_for_status()
    logger.info("Sent photo to Max: %s", resp.json())


async def handle_channel_post(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle new channel posts and forward them to Max."""
    post = update.channel_post
    if post is None:
        return

    async with httpx.AsyncClient(timeout=30) as client:
        if post.photo:
            # Get the largest available photo
            photo = post.photo[-1]
            tg_file = await context.bot.get_file(photo.file_id)

            buf = io.BytesIO()
            await tg_file.download_to_memory(buf)
            photo_bytes = buf.getvalue()

            upload_result = await upload_max_photo(
                client, photo_bytes, f"{photo.file_id}.jpg"
            )
            await send_max_photo(client, upload_result, caption=post.caption)
        elif post.text:
            await send_max_text(client, post.text)
        else:
            logger.info("Skipping unsupported channel post type")


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post)
    )
    logger.info("Bot started, polling for channel posts...")
    app.run_polling(allowed_updates=[Update.CHANNEL_POST])


if __name__ == "__main__":
    main()
