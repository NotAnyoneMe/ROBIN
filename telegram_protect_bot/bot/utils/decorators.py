import functools
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError

from telegram_protect_bot.config import messages
from telegram_protect_bot.bot.utils import permissions
from telegram_protect_bot.database import operations as db

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
            db.add_log(
                action="error",
                user_id=event.sender_id,
                group_id=None if event.is_private else event.chat_id,
                details=f"Error in {func.__name__}: {error_message}"
            )
    return wrapper