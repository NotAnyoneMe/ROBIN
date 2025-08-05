from telethon import TelegramClient
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

from telegram_protect_bot.config import settings
from telegram_protect_bot.database import operations as db

async def is_user_admin(client, chat_id, user_id):
    """Check if a user is an admin in a chat."""
    try:
        # First check database cache
        if db.is_admin(user_id, chat_id):
            return True
            
        # If not in cache, check with Telegram API
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=user_id
        ))
        
        is_admin = isinstance(participant.participant, (ChannelParticipantCreator, ChannelParticipantAdmin))
        
        # Update database cache
        if is_admin:
            admin_title = getattr(participant.participant, 'admin_rights', None)
            db.add_user_to_group(user_id, chat_id, is_admin=True, admin_title=str(admin_title))
            
        return is_admin
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

async def is_bot_admin(client, chat_id):
    """Check if the bot is an admin in a chat."""
    try:
        bot_id = (await client.get_me()).id
        return await is_user_admin(client, chat_id, bot_id)
    except Exception as e:
        print(f"Error checking bot admin status: {e}")
        return False

async def get_chat_admins(client, chat_id):
    """Get all admins in a chat."""
    try:
        # First check database cache
        admins = db.get_group_admins(chat_id)
        if admins:
            return [admin.id for admin in admins]
            
        # If not in cache, get from Telegram API
        admin_participants = await client.get_participants(
            chat_id,
            filter=ChannelParticipantsAdmins
        )
        
        admin_ids = []
        for admin in admin_participants:
            admin_ids.append(admin.id)
            # Update database
            db.add_user_to_group(
                admin.id, 
                chat_id, 
                is_admin=True,
                admin_title=getattr(admin, 'admin_title', None)
            )
            
        return admin_ids
    except Exception as e:
        print(f"Error getting chat admins: {e}")
        return []

async def can_delete_messages(client, chat_id):
    """Check if the bot can delete messages in a chat."""
    try:
        bot_id = (await client.get_me()).id
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=bot_id
        ))
        
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
            
        if isinstance(participant.participant, ChannelParticipantAdmin):
            admin_rights = participant.participant.admin_rights
            return admin_rights.delete_messages
            
        return False
    except Exception as e:
        print(f"Error checking delete permissions: {e}")
        return False

async def can_ban_users(client, chat_id):
    """Check if the bot can ban users in a chat."""
    try:
        bot_id = (await client.get_me()).id
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=bot_id
        ))
        
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
            
        if isinstance(participant.participant, ChannelParticipantAdmin):
            admin_rights = participant.participant.admin_rights
            return admin_rights.ban_users
            
        return False
    except Exception as e:
        print(f"Error checking ban permissions: {e}")
        return False

async def can_invite_users(client, chat_id):
    """Check if the bot can invite users to a chat."""
    try:
        bot_id = (await client.get_me()).id
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=bot_id
        ))
        
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
            
        if isinstance(participant.participant, ChannelParticipantAdmin):
            admin_rights = participant.participant.admin_rights
            return admin_rights.invite_users
            
        return False
    except Exception as e:
        print(f"Error checking invite permissions: {e}")
        return False

async def can_pin_messages(client, chat_id):
    """Check if the bot can pin messages in a chat."""
    try:
        bot_id = (await client.get_me()).id
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=bot_id
        ))
        
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
            
        if isinstance(participant.participant, ChannelParticipantAdmin):
            admin_rights = participant.participant.admin_rights
            return admin_rights.pin_messages
            
        return False
    except Exception as e:
        print(f"Error checking pin permissions: {e}")
        return False

async def can_change_info(client, chat_id):
    """Check if the bot can change chat info."""
    try:
        bot_id = (await client.get_me()).id
        participant = await client(GetParticipantRequest(
            channel=chat_id,
            participant=bot_id
        ))
        
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
            
        if isinstance(participant.participant, ChannelParticipantAdmin):
            admin_rights = participant.participant.admin_rights
            return admin_rights.change_info
            
        return False
    except Exception as e:
        print(f"Error checking change info permissions: {e}")
        return False

def is_owner(user_id):
    """Check if a user is the bot owner."""
    return user_id == settings.OWNER_ID

def is_sudo_user(user_id):
    """Check if a user is a sudo user."""
    return user_id in settings.SUDO_USERS or user_id == settings.OWNER_ID

def is_admin_user(user_id):
    """Check if a user is an admin user."""
    return user_id in settings.ADMIN_IDS or is_sudo_user(user_id)