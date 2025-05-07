import os
import json
import logging
import re
from typing import Dict, List, Optional, Any
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from instagram_monitor import InstagramMonitor
import asyncio
import signal
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Add security headers
Talisman(app, content_security_policy=None)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize bot and application
bot_token = os.getenv('BOT_TOKEN')
if not bot_token:
    raise ValueError("BOT_TOKEN environment variable is required")

# Build the Application with proper defaults
application = (
    Application.builder()
    .token(bot_token)
    .concurrent_updates(True)
    .build()
)

# Initialize Instagram monitor
monitor = None

def load_users() -> Dict[str, List[str]]:
    """Load users from the users file."""
    if not os.path.exists("users.json"):
        return {}
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logger.error(f"Error loading users: {e}")
        return {}

def save_users(users: Dict[str, List[str]]) -> None:
    """Save users to the users file."""
    try:
        with open("users.json", "w") as f:
            json.dump(users, f)
    except (PermissionError, IOError) as e:
        logger.error(f"Error saving users: {e}")

def validate_username(username: str) -> bool:
    """Validate Instagram username format."""
    if not username or not username.strip():
        return False
    username = username.strip().lower()
    # Instagram usernames can only contain letters, numbers, periods, and underscores
    return bool(re.match(r'^[a-zA-Z0-9._]+$', username))

def add_user(chat_id: str, username: str) -> bool:
    """Add a user to the tracking list."""
    if not validate_username(username):
        return False
        
    users = load_users()
    if str(chat_id) not in users:
        users[str(chat_id)] = []
    if username not in users[str(chat_id)]:
        users[str(chat_id)].append(username)
        save_users(users)
        return True
    return False

def remove_user(chat_id: str, username: str) -> bool:
    """Remove a user from the tracking list."""
    if not validate_username(username):
        return False
        
    users = load_users()
    if str(chat_id) in users and username in users[str(chat_id)]:
        users[str(chat_id)].remove(username)
        if not users[str(chat_id)]:
            del users[str(chat_id)]
        save_users(users)
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎭 <b>Welcome to the Instagram Story Stalker Bot!</b>\n\n"
             "Oh great, another person who can't resist the urge to know what others are doing 24/7. Don't worry, we won't judge... much. 😏\n\n"
             "Here's what you can do with me (because apparently, you have nothing better to do):\n\n"
             "🔍 <b>Track Stories:</b>\n"
             "/track username - Start stalking someone's stories\n"
             "Example: /track instagram\n\n"
             "📥 <b>Download Stories:</b>\n"
             "/download username - Download someone's current story\n"
             "Example: /download kimkardashian\n\n"
             "🚫 <b>Stop Stalking:</b>\n"
             "/untrack username - Stop being creepy (or at least pretend to)\n\n"
             "📋 <b>Your Stalking List:</b>\n"
             "/list - See who you're currently obsessing over\n\n"
             "📊 <b>Stalking Stats:</b>\n"
             "/stats - Check how much of your life you've wasted here\n\n"
             "🏆 <b>Stalking Level:</b>\n"
             "/level - See how deep into the stalking rabbit hole you are\n\n"
             "🔥 <b>Get Roasted:</b>\n"
             "/roast - Get roasted for your questionable life choices\n\n"
             "🎯 <b>Pro Tips:</b>\n"
             "/tips - Learn how to be a better stalker (we're not proud of this)\n\n"
             "🏅 <b>Stalking Achievements:</b>\n"
             "/achievements - Collect badges for your dedication to being nosy\n\n"
             "❓ <b>Need Help?</b>\n"
             "/help - Get this message again (because you probably forgot already)\n\n"
             "<i>Remember: Just because you can stalk someone's stories doesn't mean you should... but who are we to stop you? 🤷‍♂️</i>",
        parse_mode="HTML"
    )

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /track command."""
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Please provide an Instagram username to track.\n"
                 "Example: /track instagram",
            parse_mode="HTML"
        )
        return

    username = context.args[0].lower()
    if not validate_username(username):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Invalid Instagram username format.\n"
                 "Usernames can only contain letters, numbers, periods, and underscores.",
            parse_mode="HTML"
        )
        return

    if add_user(chat_id, username):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Now tracking {username}!\n"
                 "You'll be notified when they post new stories. 🎭",
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"ℹ️ You're already tracking {username}!",
            parse_mode="HTML"
        )

async def untrack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /untrack command."""
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Please provide an Instagram username to stop tracking.\n"
                 "Example: /untrack instagram",
            parse_mode="HTML"
        )
        return

    username = context.args[0].lower()
    if not validate_username(username):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Invalid Instagram username format.\n"
                 "Usernames can only contain letters, numbers, periods, and underscores.",
            parse_mode="HTML"
        )
        return

    if remove_user(chat_id, username):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Stopped tracking {username}.",
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"ℹ️ You weren't tracking {username}.",
            parse_mode="HTML"
        )

async def list_tracked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /list command."""
    chat_id = update.effective_chat.id
    users = load_users()
    tracked = users.get(str(chat_id), [])
    
    if not tracked:
        await context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ You're not tracking any Instagram accounts yet.\n"
                 "Use /track username to start tracking.",
            parse_mode="HTML"
        )
    else:
        message = "📋 <b>You're tracking these Instagram accounts:</b>\n\n"
        message += "\n".join([f"• {username}" for username in tracked])
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML"
        )

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /download command."""
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Please provide an Instagram username to download stories from.\n"
                 "Example: /download kimkardashian",
            parse_mode="HTML"
        )
        return

    username = context.args[0].lower()
    if not validate_username(username):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Invalid Instagram username format.\n"
                 "Usernames can only contain letters, numbers, periods, and underscores.",
            parse_mode="HTML"
        )
        return

    # Send initial message
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🔄 Checking stories for {username}...\n"
             "This might take a moment while I do my sneaky business. 👀",
        parse_mode="HTML"
    )

    try:
        # Initialize monitor
        global monitor
        if not monitor:
            monitor = InstagramMonitor()
            await monitor.__aenter__()
        
        # Check for stories
        story_data = await monitor.check_story(username)
        
        if not story_data or not story_data.get("stories"):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"😴 No active stories found for {username}.\n\n"
                     "Your collection of sadness is empty. Maybe they're:\n"
                     "• Living their best life offline (unlike you)\n"
                     "• Actually being productive (unlike you)\n"
                     "• Just not interested in sharing their life with random stalkers (like you)\n\n"
                     "Try again later when they're actually doing something interesting. Or maybe... get a life? 🤷‍♂️",
                parse_mode="HTML"
            )
            return

        # For now, just report how many stories were found
        num_stories = len(story_data.get("stories", []))
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Found {num_stories} active {'story' if num_stories == 1 else 'stories'} for {username}!\n\n"
                 f"🚧 Story download feature is coming soon.\n"
                 f"For now, we'll notify you when {username} posts new stories.",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error downloading story for {username}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error downloading story: {str(e)}\n"
                 "Maybe try again later? Or maybe you should just... stop stalking? 🤷‍♂️",
            parse_mode="HTML"
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="📊 Stats coming soon!",
        parse_mode="HTML"
    )

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🏆 Level system coming soon!",
        parse_mode="HTML"
    )

async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🔥 Roasting system coming soon!",
        parse_mode="HTML"
    )

async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎯 Tips coming soon!",
        parse_mode="HTML"
    )

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text="🏅 Achievements coming soon!",
        parse_mode="HTML"
    )

async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ An error occurred. Please try again later.",
            parse_mode="HTML"
        )

async def cleanup() -> None:
    """Clean up resources."""
    global monitor
    logger.info("Cleaning up resources...")
    
    try:
        if monitor:
            logger.info("Closing Instagram monitor...")
            await monitor.__aexit__(None, None, None)
            monitor = None
            logger.info("Instagram monitor resources cleaned up")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(sig, frame):
    """Handle signals to gracefully shut down."""
    print("\nReceived shutdown signal, cleaning up...")
    
    # Stop the application if it's running
    if hasattr(application, "is_running") and application.is_running:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cleanup())
        application.stop()
    
    # Exit gracefully
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("track", track))
application.add_handler(CommandHandler("untrack", untrack))
application.add_handler(CommandHandler("list", list_tracked))
application.add_handler(CommandHandler("download", download))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("level", level))
application.add_handler(CommandHandler("roast", roast))
application.add_handler(CommandHandler("tips", tips))
application.add_handler(CommandHandler("achievements", achievements))
application.add_handler(CommandHandler("help", start))  # Reuse start command for help
application.add_error_handler(error_handler)

@app.route('/webhook', methods=['POST'])
@limiter.limit("5 per second")
def webhook():
    """Handle incoming webhook updates."""
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            
            # Process update in the application that was already initialized
            application.create_task(application.process_update(update))
            
            return "ok"
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            return "error", 500
    return "method not allowed", 405

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return "ok"

@app.route('/test')
def test():
    """Test endpoint."""
    return "Bot is running!"

def run_polling():
    """Run the bot in polling mode."""
    # Delete any existing webhook
    import requests
    
    try:
        # Delete webhook and drop pending updates
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
            params={'drop_pending_updates': True}
        )
        print("Webhook deleted, starting the Instagram Story Stalker Bot in polling mode...")
        
        # Start the Bot with polling
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error in polling mode: {e}")
    finally:
        print("Bot stopped.")

def run_webhook():
    """Run the bot in webhook mode."""
    # Start the Flask app
    port = int(os.getenv('PORT', 5005))
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        # Set webhook
        import requests
        webhook_path = f"{webhook_url}/webhook"
        
        # Initialize the application before setting the webhook
        application.initialize()
        
        # Set webhook with proper parameters
        requests.get(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            params={
                'url': webhook_path,
                'allowed_updates': ['message', 'callback_query'],
                'drop_pending_updates': True
            }
        )
        print(f"Webhook set to {webhook_path}, starting the Instagram Story Stalker Bot in webhook mode...")
        
        # Register webhook for receiving updates
        application.bot.setWebhook(url=webhook_path)
        
        # Start the Flask server
        app.run(host='0.0.0.0', port=port)
    else:
        print("WEBHOOK_URL environment variable not set. Falling back to polling mode.")
        run_polling()

if __name__ == '__main__':
    # Determine if we should use webhook or polling
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    
    try:
        if use_webhook:
            run_webhook()
        else:
            run_polling()
    finally:
        # Ensure we clean up resources
        asyncio.run(cleanup())

