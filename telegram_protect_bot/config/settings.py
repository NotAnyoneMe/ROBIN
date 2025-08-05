import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Telegram API Configuration
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
BOT_NAME = os.getenv('BOT_NAME', 'Protection Bot')

# Admin Configuration
OWNER_ID = int(os.getenv('OWNER_ID', 0))
OWNER_USERNAME = os.getenv('OWNER_USERNAME', '')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', 0))
SUPPORT_CHAT_ID = int(os.getenv('SUPPORT_CHAT_ID', 0))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))

# Admin IDs
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv('ADMIN_IDS', '').split(',') if admin_id]
SUDO_USERS = [int(sudo_id) for sudo_id in os.getenv('SUDO_USERS', '').split(',') if sudo_id]

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
ERROR_LOG_FILE = os.getenv('ERROR_LOG_FILE', 'logs/error.log')

# Anti-Spam Settings
DEFAULT_MESSAGE_LIMIT = int(os.getenv('DEFAULT_MESSAGE_LIMIT', 10))
DEFAULT_MESSAGE_WINDOW = int(os.getenv('DEFAULT_MESSAGE_WINDOW', 60))
DEFAULT_FORWARD_LIMIT = int(os.getenv('DEFAULT_FORWARD_LIMIT', 5))
DEFAULT_FORWARD_WINDOW = int(os.getenv('DEFAULT_FORWARD_WINDOW', 3600))
DEFAULT_MENTION_LIMIT = int(os.getenv('DEFAULT_MENTION_LIMIT', 5))
DEFAULT_LINK_LIMIT = int(os.getenv('DEFAULT_LINK_LIMIT', 3))

# Auto-Ban Thresholds
SPAM_SCORE_THRESHOLD = int(os.getenv('SPAM_SCORE_THRESHOLD', 75))
AUTO_BAN_SCORE = int(os.getenv('AUTO_BAN_SCORE', 90))
WARNING_THRESHOLD = int(os.getenv('WARNING_THRESHOLD', 3))
RAID_THRESHOLD = int(os.getenv('RAID_THRESHOLD', 10))

# Content Filtering
ENABLE_LINK_FILTERING = os.getenv('ENABLE_LINK_FILTERING', 'true').lower() == 'true'
ENABLE_MEDIA_FILTERING = os.getenv('ENABLE_MEDIA_FILTERING', 'false').lower() == 'true'
ENABLE_LANGUAGE_DETECTION = os.getenv('ENABLE_LANGUAGE_DETECTION', 'true').lower() == 'true'
ENABLE_NSFW_DETECTION = os.getenv('ENABLE_NSFW_DETECTION', 'true').lower() == 'true'
ENABLE_SCAM_DETECTION = os.getenv('ENABLE_SCAM_DETECTION', 'true').lower() == 'true'

# Time Limits (in seconds)
DEFAULT_MUTE_TIME = int(os.getenv('DEFAULT_MUTE_TIME', 3600))
DEFAULT_BAN_TIME = int(os.getenv('DEFAULT_BAN_TIME', 86400))
MAX_MUTE_TIME = int(os.getenv('MAX_MUTE_TIME', 604800))
MAX_BAN_TIME = int(os.getenv('MAX_BAN_TIME', 2592000))

# Welcome & Notification Settings
DEFAULT_WELCOME_MESSAGE = os.getenv('DEFAULT_WELCOME_MESSAGE', 'Welcome {mention} to {chat_title}! Please read the rules.')
DEFAULT_GOODBYE_MESSAGE = os.getenv('DEFAULT_GOODBYE_MESSAGE', '{mention} left {chat_title}')
DEFAULT_RULES_MESSAGE = os.getenv('DEFAULT_RULES_MESSAGE', 'Please follow the group rules and be respectful.')

# Notification Settings
ENABLE_WELCOME_MESSAGES = os.getenv('ENABLE_WELCOME_MESSAGES', 'true').lower() == 'true'
ENABLE_GOODBYE_MESSAGES = os.getenv('ENABLE_GOODBYE_MESSAGES', 'true').lower() == 'true'
ENABLE_JOIN_NOTIFICATIONS = os.getenv('ENABLE_JOIN_NOTIFICATIONS', 'true').lower() == 'true'
ENABLE_LEAVE_NOTIFICATIONS = os.getenv('ENABLE_LEAVE_NOTIFICATIONS', 'false').lower() == 'true'
ENABLE_PROMOTION_NOTIFICATIONS = os.getenv('ENABLE_PROMOTION_NOTIFICATIONS', 'true').lower() == 'true'

# Message Cleanup
AUTO_DELETE_WELCOME_TIME = int(os.getenv('AUTO_DELETE_WELCOME_TIME', 300))
AUTO_DELETE_COMMANDS = os.getenv('AUTO_DELETE_COMMANDS', 'true').lower() == 'true'
COMMAND_DELETE_DELAY = int(os.getenv('COMMAND_DELETE_DELAY', 30))

# Ensure required directories exist
os.makedirs(Path(__file__).parent.parent / 'logs', exist_ok=True)
os.makedirs(Path(__file__).parent.parent / 'data', exist_ok=True)