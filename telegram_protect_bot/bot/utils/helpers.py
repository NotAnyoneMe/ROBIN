import re
import time
from datetime import datetime, timedelta
import validators
from telethon.tl.types import User as TelegramUser, Channel, Chat
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from langdetect import detect, LangDetectException

from telegram_protect_bot.config import settings

def get_user_link(user):
    """Get a markdown link to a user."""
    if not user:
        return "Unknown User"
        
    user_id = user.id
    name = get_full_name(user)
    
    return f"[{name}](tg://user?id={user_id})"

def get_full_name(user):
    """Get the full name of a user."""
    if not user:
        return "Unknown User"
        
    if isinstance(user, TelegramUser):
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        elif user.first_name:
            return user.first_name
        elif user.username:
            return user.username
        else:
            return f"User {user.id}"
    else:
        # Handle case where user is a dict or other object
        first_name = getattr(user, 'first_name', None)
        last_name = getattr(user, 'last_name', None)
        username = getattr(user, 'username', None)
        user_id = getattr(user, 'id', 'Unknown')
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif username:
            return username
        else:
            return f"User {user_id}"

def get_chat_title(chat):
    """Get the title of a chat."""
    if not chat:
        return "Unknown Chat"
        
    if isinstance(chat, (Channel, Chat)):
        return chat.title
    else:
        # Handle case where chat is a dict or other object
        return getattr(chat, 'title', 'Unknown Chat')

async def get_chat_member_count(client, chat_id):
    """Get the number of members in a chat."""
    try:
        if str(chat_id).startswith('-100'):
            # Supergroup or channel
            full_channel = await client(GetFullChannelRequest(channel=chat_id))
            return full_channel.full_chat.participants_count
        else:
            # Normal group
            full_chat = await client(GetFullChatRequest(chat_id=chat_id))
            return len(full_chat.users)
    except Exception as e:
        print(f"Error getting member count: {e}")
        return 0

def parse_time(time_str):
    """Parse a time string into seconds."""
    if not time_str:
        return None
        
    time_str = time_str.lower()
    
    # If it's just a number, assume seconds
    if time_str.isdigit():
        return int(time_str)
        
    # Parse time with units
    time_regex = re.compile(r'(\d+)([smhd])')
    matches = time_regex.findall(time_str)
    
    if not matches:
        return None
        
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 's':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
            
    return total_seconds

def format_time_delta(seconds):
    """Format a time delta in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"

def format_time_duration(seconds):
    """Format a time duration in seconds to a detailed human-readable string."""
    if not seconds:
        return "indefinitely"
        
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"

def is_time_format(text):
    """Check if a string is in a valid time format."""
    if not text:
        return False
        
    # Check if it's just a number (seconds)
    if text.isdigit():
        return True
        
    # Check for time with units (e.g., 1h, 30m, 1d)
    time_regex = re.compile(r'^(\d+[smhd])+$')
    return bool(time_regex.match(text))

def is_valid_url(text):
    """Check if a text contains a valid URL."""
    # Simple URL regex
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    # Check with regex first
    if url_pattern.search(text):
        # Validate with validators library
        urls = url_pattern.findall(text)
        for url in urls:
            if validators.url(url):
                return True
                
    return False

def contains_mention(text):
    """Check if a text contains a mention."""
    mention_pattern = re.compile(r'@\w+')
    return bool(mention_pattern.search(text))

def count_mentions(text):
    """Count the number of mentions in a text."""
    mention_pattern = re.compile(r'@\w+')
    return len(mention_pattern.findall(text))

def detect_language(text):
    """Detect the language of a text."""
    try:
        if len(text) < 10:  # Too short to reliably detect
            return None
        return detect(text)
    except LangDetectException:
        return None

def contains_blacklisted_words(text, blacklist):
    """Check if a text contains blacklisted words."""
    if not blacklist:
        return False
        
    text = text.lower()
    for word in blacklist:
        if word.lower() in text:
            return True
            
    return False

def extract_user_and_reason(message):
    """Extract user ID/username and reason from a command."""
    args = message.text.split(None, 2)
    
    if len(args) < 2:
        return None, None
        
    user = args[1]
    reason = args[2] if len(args) > 2 else None
    
    # Check if user is a mention or ID
    user_id = None
    
    if user.isdigit():
        user_id = int(user)
    elif user.startswith('@'):
        user_id = user  # Username
    elif len(message.entities) > 1:
        # Check for user mention entity
        for entity in message.entities:
            if entity.offset > 0:  # Skip the command entity
                user_id = message.text[entity.offset:entity.offset+entity.length]
                break
                
    return user_id, reason

def rate_limit_check(user_id, action_type, limit, window):
    """
    Check if a user has exceeded a rate limit.
    
    Args:
        user_id: The user's ID
        action_type: Type of action (e.g., 'message', 'forward')
        limit: Maximum number of actions allowed
        window: Time window in seconds
        
    Returns:
        bool: True if rate limit exceeded, False otherwise
    """
    # This is a simple in-memory rate limiting implementation
    # In a production environment, you might want to use Redis or another cache
    
    # Initialize rate limit storage if not exists
    if not hasattr(rate_limit_check, 'limits'):
        rate_limit_check.limits = {}
        
    # Create key for this user and action
    key = f"{user_id}:{action_type}"
    
    # Get current time
    current_time = time.time()
    
    # Initialize or get user's actions
    if key not in rate_limit_check.limits:
        rate_limit_check.limits[key] = []
        
    # Clean up old actions outside the window
    rate_limit_check.limits[key] = [
        action_time for action_time in rate_limit_check.limits[key]
        if current_time - action_time <= window
    ]
    
    # Check if limit exceeded
    if len(rate_limit_check.limits[key]) >= limit:
        return True
        
    # Add current action
    rate_limit_check.limits[key].append(current_time)
    
    return False

def format_welcome_message(message_template, user, chat):
    """Format a welcome message with variables."""
    if not message_template:
        message_template = settings.DEFAULT_WELCOME_MESSAGE
        
    # Get user information
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username or ""
    mention = get_user_link(user)
    
    # Get chat information
    chat_id = chat.id
    chat_title = get_chat_title(chat)
    
    # Replace variables
    message = message_template
    message = message.replace('{user_id}', str(user_id))
    message = message.replace('{first_name}', first_name)
    message = message.replace('{last_name}', last_name)
    message = message.replace('{username}', username)
    message = message.replace('{mention}', mention)
    message = message.replace('{chat_id}', str(chat_id))
    message = message.replace('{chat_title}', chat_title)
    
    return message

def format_goodbye_message(message_template, user, chat):
    """Format a goodbye message with variables."""
    if not message_template:
        message_template = settings.DEFAULT_GOODBYE_MESSAGE
        
    # Get user information
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = user.username or ""
    mention = get_user_link(user)
    
    # Get chat information
    chat_id = chat.id
    chat_title = get_chat_title(chat)
    
    # Replace variables
    message = message_template
    message = message.replace('{user_id}', str(user_id))
    message = message.replace('{first_name}', first_name)
    message = message.replace('{last_name}', last_name)
    message = message.replace('{username}', username)
    message = message.replace('{mention}', mention)
    message = message.replace('{chat_id}', str(chat_id))
    message = message.replace('{chat_title}', chat_title)
    
    return message