import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from telegram_protect_bot.bot.client import BotClient
from telegram_protect_bot.config import settings, validator
from telegram_protect_bot.database import operations as db

# Import handlers
from telegram_protect_bot.bot.handlers import welcome, antispam, admin, callback
from telegram_protect_bot.bot.commands import user, settings as settings_commands, admin as admin_commands

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
    # Validate configuration
    if not validator.validate_config():
        logger.error("Invalid configuration. Please check your settings and try again.")
        return
    
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
    try:
        await welcome.setup(client)
        await antispam.setup(client)
        await admin.setup(client)
        callback.register_handlers(client)
        
        # Set up commands
        await user.setup(client)
        await settings_commands.setup(client)
        await admin_commands.setup(client)
    except Exception as e:
        logger.error(f"Error setting up handlers: {e}", exc_info=True)
        return
    
    # Log successful startup
    logger.info(f"Bot started successfully as @{settings.BOT_USERNAME}")
    
    # Send startup notification
    try:
        me = await client.client.get_me()
        startup_message = f"🤖 **Bot Started**\n\nUsername: @{me.username}\nID: `{me.id}`\nName: {me.first_name}\nVersion: 1.0.0"
        await client.send_message_to_log_channel(startup_message)
    except Exception as e:
        logger.error(f"Error sending startup notification: {e}")
    
    # Run the client
    await client.client.run_until_disconnected()

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(Path(__file__).parent / 'logs', exist_ok=True)
    os.makedirs(Path(__file__).parent / 'data', exist_ok=True)
    
    # Run the bot
    asyncio.run(main())