"""
Input validation utilities for the Telegram Protection Bot.
"""

import re
from typing import Optional, Dict, Any, Union, List

def validate_username(username: str) -> bool:
    """
    Validate a Telegram username.
    
    Args:
        username: The username to validate
        
    Returns:
        bool: True if the username is valid, False otherwise
    """
    if not username:
        return False
    
    # Username must start with @
    if not username.startswith('@'):
        return False
    
    # Username must be 5-32 characters long (including @)
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Username can only contain a-z, 0-9, and underscores
    if not re.match(r'^@[a-z0-9_]+$', username):
        return False
    
    return True

def validate_user_id(user_id: Union[str, int]) -> bool:
    """
    Validate a Telegram user ID.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        bool: True if the user ID is valid, False otherwise
    """
    try:
        # Convert to int if it's a string
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        # User ID must be positive
        return user_id > 0
    except ValueError:
        return False

def validate_chat_id(chat_id: Union[str, int]) -> bool:
    """
    Validate a Telegram chat ID.
    
    Args:
        chat_id: The chat ID to validate
        
    Returns:
        bool: True if the chat ID is valid, False otherwise
    """
    try:
        # Convert to int if it's a string
        if isinstance(chat_id, str):
            chat_id = int(chat_id)
        
        # Group chat IDs are negative
        return chat_id < 0
    except ValueError:
        return False

def validate_command_args(args: List[str], min_args: int = 0, max_args: Optional[int] = None) -> bool:
    """
    Validate command arguments.
    
    Args:
        args: The command arguments to validate
        min_args: The minimum number of arguments required
        max_args: The maximum number of arguments allowed (None for no limit)
        
    Returns:
        bool: True if the arguments are valid, False otherwise
    """
    if len(args) < min_args:
        return False
    
    if max_args is not None and len(args) > max_args:
        return False
    
    return True

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: The text to sanitize
        
    Returns:
        str: The sanitized text
    """
    # Remove control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    
    # Escape HTML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text