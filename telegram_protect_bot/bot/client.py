import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

from telegram_protect_bot.config import settings
from telegram_protect_bot.database import operations as db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL),
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BotClient:
    """Telegram client wrapper for the protection bot."""
    
    def __init__(self, session=None):
        """Initialize the bot client."""
        self.client = TelegramClient(
            session or 'bot_session',
            settings.API_ID,
            settings.API_HASH
        )
        
        # Initialize handlers dictionary
        self.handlers = {}
        
    async def start(self):
        """Start the bot client."""
        try:
            # Start the client
            await self.client.start(bot_token=settings.BOT_TOKEN)
            
            # Get bot information
            me = await self.client.get_me()
            logger.info(f"Bot started as @{me.username} ({me.id})")
            
            # Initialize database
            db.init_db()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return False
            
    async def run(self):
        """Run the bot client."""
        await self.start()
        
        # Run the client until disconnected
        await self.client.run_until_disconnected()
        
    def add_event_handler(self, callback, event):
        """Add an event handler to the client."""
        handler = self.client.add_event_handler(callback, event)
        self.handlers[callback.__name__] = handler
        return handler
        
    def remove_event_handler(self, callback):
        """Remove an event handler from the client."""
        if callback.__name__ in self.handlers:
            self.client.remove_event_handler(self.handlers[callback.__name__])
            del self.handlers[callback.__name__]
            
    async def send_message_to_log_channel(self, message):
        """Send a message to the log channel."""
        if hasattr(settings, 'LOG_CHANNEL_ID') and settings.LOG_CHANNEL_ID:
            try:
                await self.client.send_message(settings.LOG_CHANNEL_ID, message)
                return True
            except Exception as e:
                logger.error(f"Failed to send message to log channel: {e}")
                return False
        logger.info(f"Log message (no channel): {message}")
        return False
        
    async def send_admin_notification(self, message):
        """Send a notification to the admin chat."""
        if hasattr(settings, 'ADMIN_CHAT_ID') and settings.ADMIN_CHAT_ID:
            try:
                await self.client.send_message(settings.ADMIN_CHAT_ID, message)
                return True
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
                return False
        logger.info(f"Admin notification (no channel): {message}")
        return False