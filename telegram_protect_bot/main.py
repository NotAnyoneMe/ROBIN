import asyncio
import logging
import os
from pathlib import Path

from telegram_protect_bot.bot.client import BotClient
from telegram_protect_bot.config import settings
from telegram_protect_bot.database import operations as db

# Import handlers
from telegram_protect_bot.bot.handlers import welcome, antispam, admin
from telegram_protect_bot.bot.commands import user, settings as settings_commands

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

async def main():
    """Main function to start the bot."""
    # Create client
    client = BotClient()
    
    # Start the client
    started = await client.start()
    if not started:
        logger.error("Failed to start the bot. Exiting...")
        return
        
    # Initialize database
    db.init_db()
    
    # Set up handlers
    await welcome.setup(client)
    await antispam.setup(client)
    await admin.setup(client)
    
    # Set up commands
    await user.setup(client)
    await settings_commands.setup(client)
    
    # Log successful startup
    logger.info(f"Bot started successfully as @{settings.BOT_USERNAME}")
    
    # Send startup notification
    me = await client.client.get_me()
    startup_message = f"🤖 **Bot Started**\n\nUsername: @{me.username}\nID: `{me.id}`\nName: {me.first_name}\nVersion: 1.0.0"
    await client.send_message_to_log_channel(startup_message)
    
    # Run the client
    await client.client.run_until_disconnected()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(Path(__file__).parent / 'logs', exist_ok=True)
    os.makedirs(Path(__file__).parent / 'data', exist_ok=True)
    
    # Run the bot
    asyncio.run(main())