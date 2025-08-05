from telethon import events
import asyncio

from telegram_protect_bot.config import settings
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, decorators

async def setup(client):
    """Set up welcome message handlers."""
    
    @client.add_event_handler
    @decorators.handle_errors
    async def on_user_join(event):
        """Handle user join events."""
        if not event.user_joined and not event.user_added:
            return
            
        # Get chat and user information
        chat_id = event.chat_id
        chat = await event.get_chat()
        user = await event.get_user()
        
        # Update database
        db.get_or_create_group(chat_id, chat.title, getattr(chat, 'username', None))
        db.get_or_create_user(
            user.id,
            user.first_name,
            user.last_name,
            user.username,
            user.bot
        )
        db.add_user_to_group(user.id, chat_id)
        
        # Log the join
        db.add_log(
            action="user_joined",
            group_id=chat_id,
            user_id=user.id
        )
        
        # Check group settings
        group_settings = db.get_group_settings(chat_id)
        if not group_settings or not group_settings.welcome_enabled:
            return
            
        # Format welcome message
        welcome_message = helpers.format_welcome_message(
            group_settings.welcome_message,
            user,
            chat
        )
        
        # Send welcome message
        welcome_msg = await event.reply(welcome_message, parse_mode='md')
        
        # Auto-delete welcome message if enabled
        if group_settings.auto_delete_welcome_time > 0:
            await asyncio.sleep(group_settings.auto_delete_welcome_time)
            try:
                await welcome_msg.delete()
            except Exception as e:
                print(f"Error deleting welcome message: {e}")
                
        # Check for raid
        if settings.ENABLE_JOIN_NOTIFICATIONS and db.check_raid(
            chat_id,
            threshold=group_settings.raid_threshold,
            window=60
        ):
            # Notify admins about possible raid
            raid_message = f"🚨 **Possible Raid Detected!**\n\n{group_settings.raid_threshold}+ users joined {chat.title} in the last minute."
            await client.send_message_to_log_channel(raid_message)
    
    @client.add_event_handler
    @decorators.handle_errors
    async def on_user_leave(event):
        """Handle user leave events."""
        if not event.user_kicked and not event.user_left:
            return
            
        # Get chat and user information
        chat_id = event.chat_id
        chat = await event.get_chat()
        user = await event.get_user()
        
        # Update database
        db.remove_user_from_group(user.id, chat_id)
        
        # Log the leave
        db.add_log(
            action="user_left" if event.user_left else "user_kicked",
            group_id=chat_id,
            user_id=user.id
        )
        
        # Check group settings
        group_settings = db.get_group_settings(chat_id)
        if not group_settings or not group_settings.goodbye_enabled:
            return
            
        # Only show goodbye message for users who left, not kicked
        if event.user_left and settings.ENABLE_GOODBYE_MESSAGES:
            # Format goodbye message
            goodbye_message = helpers.format_goodbye_message(
                group_settings.goodbye_message,
                user,
                chat
            )
            
            # Send goodbye message
            goodbye_msg = await event.reply(goodbye_message, parse_mode='md')
            
            # Auto-delete goodbye message
            if group_settings.auto_delete_welcome_time > 0:
                await asyncio.sleep(group_settings.auto_delete_welcome_time)
                try:
                    await goodbye_msg.delete()
                except Exception as e:
                    print(f"Error deleting goodbye message: {e}")
    
    # Register the event handlers
    client.add_event_handler(on_user_join, events.ChatAction(func=lambda e: e.user_joined or e.user_added))
    client.add_event_handler(on_user_leave, events.ChatAction(func=lambda e: e.user_kicked or e.user_left))