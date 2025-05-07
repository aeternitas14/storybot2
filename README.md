# Instagram Story Stalker Bot 🎭

A sarcastic Telegram bot that helps you track Instagram stories with style! Built with Python, Telegram API, and a healthy dose of humor.

## Features 🎭

- Track Instagram stories of any public account
- Get instant notifications when new stories are posted
- Sarcastic responses and fun interactions
- Support for both polling and webhook modes
- Robust story change detection
- Automatic browser session management
- Comprehensive error handling

### Commands 📝

- `/start` - Get started with the bot 🎬
- `/track username` - Start tracking someone's stories 🕵️‍♂️
- `/untrack username` - Stop tracking someone's stories 🙈
- `/list` - See all accounts you're tracking 📋
- `/download username` - Download someone's current stories 📥
- `/stats` - Check your stalking statistics 📊
- `/level` - See your current stalking level 🏆
- `/roast` - Get roasted for your stalking habits 🔥
- `/tips` - Get pro stalking tips 🎯
- `/achievements` - View your stalking achievements 🏅
- `/help` - Show all available commands 💡

## Deployment 🚀

The bot can be deployed in polling mode or webhook mode.

### Prerequisites

- Python 3.9+
- Playwright
- Required Python packages in `requirements.txt`

### Environment Variables

- `BOT_TOKEN` - Your Telegram bot token
- `INSTAGRAM_USERNAME` - Instagram account username
- `INSTAGRAM_PASSWORD` - Instagram account password
- `PORT` - Server port (default: 5005)
- `USE_WEBHOOK` - Set to "true" to use webhook mode
- `WEBHOOK_URL` - Your webhook URL (if using webhook mode)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/instagram-story-stalker.git
cd instagram-story-stalker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright:
```bash
playwright install chromium
playwright install-deps
```

4. Set up environment variables:
```bash
# Set these in your environment or create a .env file
export BOT_TOKEN=your_telegram_bot_token
export INSTAGRAM_USERNAME=your_instagram_username
export INSTAGRAM_PASSWORD=your_instagram_password
```

### Running in Polling Mode (Default)

```bash
python3 run_bot.py
```

### Running in Webhook Mode

```bash
export USE_WEBHOOK=true
export WEBHOOK_URL=https://your-webhook-url.com
export PORT=5005
python3 run_bot.py
```

## Files 📁

- `run_bot.py` - Main Telegram bot server supporting both polling and webhook modes
- `instagram_monitor.py` - Instagram story monitoring
- `users.json` - User data storage
- `alert_states/` - Story state tracking
- `requirements.txt` - Required Python packages
- `Dockerfile` - Container configuration
- `fly.toml` - Deployment configuration

## License 📄

MIT License - Feel free to use it, but don't blame us for any stalking-related incidents! 🎭