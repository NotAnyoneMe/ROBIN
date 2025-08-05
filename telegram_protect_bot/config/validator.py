"""
Configuration validator for the Telegram Protection Bot.

This module validates the configuration settings to ensure they are valid
and consistent before the bot starts.
"""

import logging
import os
from typing import Dict, Any, List, Optional

from telegram_protect_bot.config import settings

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

def validate_required_settings() -> List[str]:
    """
    Validate that all required settings are present and valid.
    
    Returns:
        List[str]: A list of error messages, empty if no errors
    """
    errors = []
    
    # Required settings
    required_settings = [
        ('API_ID', int),
        ('API_HASH', str),
        ('BOT_TOKEN', str),
        ('BOT_USERNAME', str),
        ('BOT_NAME', str),
    ]
    
    for setting_name, setting_type in required_settings:
        value = getattr(settings, setting_name, None)
        if value is None:
            errors.append(f"Missing required setting: {setting_name}")
        elif not isinstance(value, setting_type):
            errors.append(f"Invalid type for {setting_name}: expected {setting_type.__name__}, got {type(value).__name__}")
    
    # Validate API_ID is a valid integer
    if hasattr(settings, 'API_ID') and isinstance(settings.API_ID, int):
        if settings.API_ID <= 0:
            errors.append("API_ID must be a positive integer")
    
    # Validate BOT_TOKEN format
    if hasattr(settings, 'BOT_TOKEN') and isinstance(settings.BOT_TOKEN, str):
        if not settings.BOT_TOKEN.strip():
            errors.append("BOT_TOKEN cannot be empty")
        elif not ':' in settings.BOT_TOKEN:
            errors.append("BOT_TOKEN has invalid format, should contain ':'")
    
    return errors

def validate_optional_settings() -> List[str]:
    """
    Validate optional settings if they are present.
    
    Returns:
        List[str]: A list of warning messages, empty if no warnings
    """
    warnings = []
    
    # Check LOG_CHANNEL_ID
    if hasattr(settings, 'LOG_CHANNEL_ID') and settings.LOG_CHANNEL_ID:
        if not isinstance(settings.LOG_CHANNEL_ID, int):
            warnings.append("LOG_CHANNEL_ID should be an integer")
    
    # Check ADMIN_CHAT_ID
    if hasattr(settings, 'ADMIN_CHAT_ID') and settings.ADMIN_CHAT_ID:
        if not isinstance(settings.ADMIN_CHAT_ID, int):
            warnings.append("ADMIN_CHAT_ID should be an integer")
    
    # Check OWNER_ID
    if hasattr(settings, 'OWNER_ID') and settings.OWNER_ID:
        if not isinstance(settings.OWNER_ID, int):
            warnings.append("OWNER_ID should be an integer")
    
    # Check ADMIN_IDS
    if hasattr(settings, 'ADMIN_IDS') and settings.ADMIN_IDS:
        if not isinstance(settings.ADMIN_IDS, (list, tuple)):
            warnings.append("ADMIN_IDS should be a list or tuple")
        else:
            for admin_id in settings.ADMIN_IDS:
                if not isinstance(admin_id, int):
                    warnings.append(f"Admin ID {admin_id} in ADMIN_IDS is not an integer")
    
    return warnings

def validate_config() -> bool:
    """
    Validate the entire configuration.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    errors = validate_required_settings()
    warnings = validate_optional_settings()
    
    # Log all errors and warnings
    for error in errors:
        logger.error(f"Configuration error: {error}")
    
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    # Return True if no errors
    return len(errors) == 0