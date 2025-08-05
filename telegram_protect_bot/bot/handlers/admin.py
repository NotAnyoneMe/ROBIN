from telethon import events
import asyncio
import time

from telegram_protect_bot.config import settings, messages
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, permissions, decorators

async def setup(client):
    """Set up admin command handlers."""
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def ban_command(event):
        """Handle /ban command."""
        # Extract user and reason
        user_id, reason = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/ban <user> [reason] [time]"
            ))
            return
            
        # Parse time if provided
        duration = None
        if reason:
            # Check if the last part of reason is a time specification
            parts = reason.split()
            if parts and helpers.parse_time(parts[-1]):
                duration = helpers.parse_time(parts[-1])
                reason = " ".join(parts[:-1])
                
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Check if user is an admin
        if await permissions.is_user_admin(client.client, chat_id, user.id):
            await event.reply(messages.USER_IS_ADMIN_ERROR)
            return
            
        # Ban the user
        try:
            await client.client.edit_permissions(
                chat_id,
                user.id,
                view_messages=False,
                until_date=None if not duration else time.time() + duration
            )
            
            # Add ban to database
            db.add_ban(user.id, chat_id, admin.id, reason, duration)
            
            # Format time text
            time_text = f"for {helpers.format_time_delta(duration)}" if duration else "permanently"
            
            # Format reason text
            reason_text = f"for: {reason}" if reason else ""
            
            # Send ban message
            ban_message = messages.BAN_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user),
                reason_text=reason_text,
                time_text=time_text
            )
            
            await event.reply(ban_message, parse_mode='md')
            
            # Log the ban
            db.add_log(
                action="ban",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id,
                details=f"Reason: {reason}, Duration: {time_text}"
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def unban_command(event):
        """Handle /unban command."""
        # Extract user
        user_id, _ = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/unban <user>"
            ))
            return
            
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Unban the user
        try:
            await client.client.edit_permissions(
                chat_id,
                user.id,
                view_messages=True
            )
            
            # Remove ban from database
            db.remove_ban(user.id, chat_id)
            
            # Send unban message
            unban_message = messages.UNBAN_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user)
            )
            
            await event.reply(unban_message, parse_mode='md')
            
            # Log the unban
            db.add_log(
                action="unban",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def kick_command(event):
        """Handle /kick command."""
        # Extract user and reason
        user_id, reason = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/kick <user> [reason]"
            ))
            return
            
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Check if user is an admin
        if await permissions.is_user_admin(client.client, chat_id, user.id):
            await event.reply(messages.USER_IS_ADMIN_ERROR)
            return
            
        # Kick the user
        try:
            # Ban and then unban to kick
            await client.client.edit_permissions(
                chat_id,
                user.id,
                view_messages=False
            )
            await client.client.edit_permissions(
                chat_id,
                user.id,
                view_messages=True
            )
            
            # Remove user from group in database
            db.remove_user_from_group(user.id, chat_id)
            
            # Format reason text
            reason_text = f"for: {reason}" if reason else ""
            
            # Send kick message
            kick_message = messages.KICK_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user),
                reason_text=reason_text
            )
            
            await event.reply(kick_message, parse_mode='md')
            
            # Log the kick
            db.add_log(
                action="kick",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id,
                details=f"Reason: {reason}"
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def mute_command(event):
        """Handle /mute command."""
        # Extract user and reason
        user_id, reason = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/mute <user> [time] [reason]"
            ))
            return
            
        # Parse time if provided
        duration = settings.DEFAULT_MUTE_TIME  # Default: 1 hour
        if reason:
            # Check if the first part of reason is a time specification
            parts = reason.split()
            if parts and helpers.parse_time(parts[0]):
                duration = helpers.parse_time(parts[0])
                reason = " ".join(parts[1:])
                
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Check if user is an admin
        if await permissions.is_user_admin(client.client, chat_id, user.id):
            await event.reply(messages.USER_IS_ADMIN_ERROR)
            return
            
        # Mute the user
        try:
            await client.client.edit_permissions(
                chat_id,
                user.id,
                until_date=time.time() + duration,
                send_messages=False
            )
            
            # Format time text
            time_text = helpers.format_time_delta(duration)
            
            # Format reason text
            reason_text = f"for: {reason}" if reason else ""
            
            # Send mute message
            mute_message = messages.MUTE_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user),
                time_text=time_text,
                reason_text=reason_text
            )
            
            await event.reply(mute_message, parse_mode='md')
            
            # Log the mute
            db.add_log(
                action="mute",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id,
                details=f"Duration: {time_text}, Reason: {reason}"
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def unmute_command(event):
        """Handle /unmute command."""
        # Extract user
        user_id, _ = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/unmute <user>"
            ))
            return
            
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Unmute the user
        try:
            await client.client.edit_permissions(
                chat_id,
                user.id,
                send_messages=True
            )
            
            # Send unmute message
            unmute_message = messages.UNMUTE_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user)
            )
            
            await event.reply(unmute_message, parse_mode='md')
            
            # Log the unmute
            db.add_log(
                action="unmute",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def warn_command(event):
        """Handle /warn command."""
        # Extract user and reason
        user_id, reason = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/warn <user> [reason]"
            ))
            return
            
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Check if user is an admin
        if await permissions.is_user_admin(client.client, chat_id, user.id):
            await event.reply(messages.USER_IS_ADMIN_ERROR)
            return
            
        # Add warning
        try:
            # Get group settings
            group_settings = db.get_group_settings(chat_id)
            warning_limit = group_settings.warning_threshold if group_settings else settings.WARNING_THRESHOLD
            
            # Add warning to database
            warning_count = db.add_warning(user.id, chat_id, admin.id, reason)
            
            # Format reason text
            reason_text = f"for: {reason}" if reason else ""
            
            # Send warn message
            warn_message = messages.WARN_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user),
                reason_text=reason_text,
                warn_count=warning_count,
                warn_limit=warning_limit
            )
            
            await event.reply(warn_message, parse_mode='md')
            
            # Log the warning
            db.add_log(
                action="warn",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id,
                details=f"Reason: {reason}, Count: {warning_count}/{warning_limit}"
            )
            
            # Auto-ban if warning threshold reached
            if warning_count >= warning_limit:
                try:
                    await client.client.edit_permissions(
                        chat_id,
                        user.id,
                        view_messages=False
                    )
                    
                    # Add ban to database
                    db.add_ban(
                        user.id,
                        chat_id,
                        admin.id,
                        f"Exceeded warning threshold ({warning_count}/{warning_limit})"
                    )
                    
                    # Send ban message
                    ban_message = f"🚫 {helpers.get_user_link(user)} has been banned for exceeding the warning threshold ({warning_count}/{warning_limit})."
                    await event.reply(ban_message, parse_mode='md')
                    
                    # Log the ban
                    db.add_log(
                        action="auto_ban",
                        group_id=chat_id,
                        user_id=user.id,
                        admin_id=admin.id,
                        details=f"Warning threshold exceeded: {warning_count}/{warning_limit}"
                    )
                    
                except Exception as e:
                    print(f"Error auto-banning user: {e}")
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.bot_admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def unwarn_command(event):
        """Handle /unwarn command."""
        # Extract user
        user_id, _ = helpers.extract_user_and_reason(event)
        if not user_id:
            await event.reply(messages.INVALID_COMMAND_FORMAT_ERROR.format(
                command_format="/unwarn <user>"
            ))
            return
            
        # Get chat and admin information
        chat_id = event.chat_id
        admin = await event.get_sender()
        
        # Try to get user information
        try:
            if isinstance(user_id, str) and user_id.startswith('@'):
                user = await client.client.get_entity(user_id)
                user_id = user.id
            else:
                user = await client.client.get_entity(int(user_id))
        except ValueError:
            await event.reply(messages.USER_NOT_FOUND_ERROR)
            return
            
        # Remove warning
        try:
            # Get group settings
            group_settings = db.get_group_settings(chat_id)
            warning_limit = group_settings.warning_threshold if group_settings else settings.WARNING_THRESHOLD
            
            # Remove warning from database
            warning_count = db.remove_warning(user.id, chat_id)
            
            if warning_count is None:
                await event.reply(f"❌ {helpers.get_user_link(user)} has no warnings to remove.", parse_mode='md')
                return
                
            # Send unwarn message
            unwarn_message = messages.UNWARN_MESSAGE.format(
                admin=helpers.get_user_link(admin),
                user_mention=helpers.get_user_link(user),
                warn_count=warning_count,
                warn_limit=warning_limit
            )
            
            await event.reply(unwarn_message, parse_mode='md')
            
            # Log the unwarn
            db.add_log(
                action="unwarn",
                group_id=chat_id,
                user_id=user.id,
                admin_id=admin.id,
                details=f"New count: {warning_count}/{warning_limit}"
            )
            
        except Exception as e:
            await event.reply(messages.GENERAL_ERROR.format(error_message=str(e)))
    
    # Register the event handlers
    client.add_event_handler(ban_command, events.NewMessage(pattern=r"^/ban(?:@\w+)?"))
    client.add_event_handler(unban_command, events.NewMessage(pattern=r"^/unban(?:@\w+)?"))
    client.add_event_handler(kick_command, events.NewMessage(pattern=r"^/kick(?:@\w+)?"))
    client.add_event_handler(mute_command, events.NewMessage(pattern=r"^/mute(?:@\w+)?"))
    client.add_event_handler(unmute_command, events.NewMessage(pattern=r"^/unmute(?:@\w+)?"))
    client.add_event_handler(warn_command, events.NewMessage(pattern=r"^/warn(?:@\w+)?"))
    client.add_event_handler(unwarn_command, events.NewMessage(pattern=r"^/unwarn(?:@\w+)?"))