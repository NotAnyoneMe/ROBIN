import functools
import re
import time
import logging
from typing import Optional, Dict, Any, List, Callable, Union
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError

from telegram_protect_bot.config import messages
from telegram_protect_bot.bot.utils import permissions, validators
from telegram_protect_bot.database import operations as db

logger = logging.getLogger(__name__)

# Store for rate limiting
_rate_limit_store: Dict[str, List[float]] = {}

def admin_required(func):
    """Decorator to check if the user is an admin in the chat."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Skip check in private chats
        if event.is_private:
            return await func(event, *args, **kwargs)
            
        # Get the user ID
        user_id = event.sender_id
        chat_id = event.chat_id
        
        # Check if user is an admin
        is_admin = await permissions.is_user_admin(event.client, chat_id, user_id)
        
        # Check if user is a bot admin/owner
        is_bot_admin = permissions.is_admin_user(user_id)
        
        if is_admin or is_bot_admin:
            return await func(event, *args, **kwargs)
        else:
            await event.reply(messages.NOT_ADMIN_ERROR)
            return None
    return wrapper

def bot_admin_required(func):
    """Decorator to check if the bot is an admin in the chat."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Skip check in private chats
        if event.is_private:
            return await func(event, *args, **kwargs)
            
        # Check if bot is an admin
        chat_id = event.chat_id
        is_admin = await permissions.is_bot_admin(event.client, chat_id)
        
        if is_admin:
            return await func(event, *args, **kwargs)
        else:
            await event.reply(messages.BOT_NOT_ADMIN_ERROR)
            return None
    return wrapper

def owner_required(func):
    """Decorator to check if the user is the bot owner."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        
        if permissions.is_owner(user_id):
            return await func(event, *args, **kwargs)
        else:
            await event.reply("❌ This command is only available to the bot owner.")
            return None
    return wrapper

def sudo_required(func):
    """Decorator to check if the user is a sudo user."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        
        if permissions.is_sudo_user(user_id):
            return await func(event, *args, **kwargs)
        else:
            await event.reply("❌ This command is only available to sudo users.")
            return None
    return wrapper

def group_only(func):
    """Decorator to ensure the command is only used in groups."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return None
        return await func(event, *args, **kwargs)
    return wrapper

def private_only(func):
    """Decorator to ensure the command is only used in private chats."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        if not event.is_private:
            await event.reply("❌ This command can only be used in private chats.")
            return None
        return await func(event, *args, **kwargs)
    return wrapper

def log_command(func):
    """Decorator to log command usage."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Extract command name from event
        command = event.text.split()[0] if event.text else "unknown"
        
        # Log command usage
        db.add_log(
            action=f"command:{command}",
            user_id=event.sender_id,
            group_id=None if event.is_private else event.chat_id,
            details=event.text
        )
        
        return await func(event, *args, **kwargs)
    return wrapper

def handle_errors(func):
    """Decorator to handle common errors."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        try:
            return await func(event, *args, **kwargs)
        except ChatAdminRequiredError:
            await event.reply(messages.BOT_NOT_ADMIN_ERROR)
        except UserAdminInvalidError:
            await event.reply(messages.USER_IS_ADMIN_ERROR)
        except Exception as e:
            error_message = str(e)
            await event.reply(messages.GENERAL_ERROR.format(error_message=error_message))
            # Log the error
            logger.error(f"Error in {func.__name__}: {error_message}", exc_info=True)
            db.add_log(
                action="error",
                user_id=event.sender_id,
                group_id=None if event.is_private else event.chat_id,
                details=f"Error in {func.__name__}: {error_message}"
            )
    return wrapper

def validate_input(pattern: Optional[str] = None, max_length: Optional[int] = None):
    """
    Decorator to validate user input.
    
    Args:
        pattern: Optional regex pattern to validate input against
        max_length: Optional maximum length for the input
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            # Get the user input
            text = event.text
            
            # Validate against pattern if provided
            if pattern and not re.match(pattern, text):
                await event.reply("❌ Invalid input format.")
                return
                
            # Check length if max_length provided
            if max_length and len(text) > max_length:
                await event.reply(f"❌ Input too long. Maximum length is {max_length} characters.")
                return
                
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit(calls: int = 5, period: int = 60):
    """
    Rate limit decorator to prevent command abuse.
    
    Args:
        calls: Maximum number of calls allowed in the period
        period: Time period in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id
            command = event.text.split()[0] if event.text else "unknown"
            key = f"{user_id}:{command}"
            current_time = time.time()
            
            if key not in _rate_limit_store:
                _rate_limit_store[key] = []
                
            # Remove timestamps older than the period
            _rate_limit_store[key] = [t for t in _rate_limit_store[key] if current_time - t < period]
            
            # Check if rate limit exceeded
            if len(_rate_limit_store[key]) >= calls:
                await event.reply(f"❌ Rate limit exceeded. Try again in {period} seconds.")
                return
                
            # Add current timestamp
            _rate_limit_store[key].append(current_time)
            
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator

def validate_args(min_args: int = 0, max_args: Optional[int] = None):
    """
    Decorator to validate command arguments.
    
    Args:
        min_args: Minimum number of arguments required
        max_args: Maximum number of arguments allowed (None for no limit)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            # Get command arguments
            command_args = event.text.split()[1:] if event.text else []
            
            # Check minimum arguments
            if len(command_args) < min_args:
                await event.reply(f"❌ This command requires at least {min_args} argument{'s' if min_args != 1 else ''}.")
                return
                
            # Check maximum arguments
            if max_args is not None and len(command_args) > max_args:
                await event.reply(f"❌ This command accepts at most {max_args} argument{'s' if max_args != 1 else ''}.")
                return
                
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator