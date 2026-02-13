# Telegram → Max Crossposting Bot

Automatically forwards messages (text and photos) from a Telegram channel to a Max messenger chat.

## Setup

### 1. Create a Telegram bot
- Message [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot` and follow the prompts
- Copy the bot token
- Add the bot as an **admin** to your Telegram channel

### 2. Create a Max bot
- Message [@MasterBot](https://max.ru/MasterBot) in Max
- Create a new bot and copy the token
- Add the bot to your target Max chat or channel

### 3. Get Max chat ID
You can discover the chat ID by calling the Max Bot API:

```
curl "https://platform-api.max.ru/chats?access_token=YOUR_MAX_BOT_TOKEN"
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your tokens and chat ID.

### 5. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Run

```bash
python bot.py
```

Post a message in your Telegram channel — it should appear in Max.
