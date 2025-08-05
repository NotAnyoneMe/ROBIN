#!/usr/bin/env python3
"""
Telegram Protection Bot - A powerful group moderation and anti-spam bot
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main function
from telegram_protect_bot.main import main

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())