from telethon import events, Button
import asyncio
import logging

from telegram_protect_bot.config import settings, messages
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, decorators, permissions

logger = logging.getLogger(__name__)

async def setup(client):
    """Set up admin command handlers."""
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def admin_command(event):
        """Handle /admin command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Create admin panel buttons
        buttons = [
            [
                Button.callback("🚫 Ban User", "ban_user:select"),
                Button.callback("👢 Kick User", "kick_user:select"),
                Button.callback("🔇 Mute User", "mute_user:select")
            ],
            [
                Button.callback("⚠️ Warn User", "warn_user:select"),
                Button.callback("📝 Note User", "note_user:select"),
                Button.callback("🔍 Check User", "check_user:select")
            ],
            [
                Button.callback("🧹 Clean Messages", "clean_messages:options"),
                Button.callback("📌 Pin Message", "pin_message"),
                Button.callback("🔓 Unpin", "unpin_message")
            ],
            [
                Button.callback("🔒 Lock Chat", "lock_chat:options"),
                Button.callback("📢 Announce", "announce:create"),
                Button.callback("⬅️ Back", "main_menu")
            ]
        ]
        
        # Send admin panel message with buttons
        await event.reply(messages.ADMIN_PANEL_TEXT, buttons=buttons, parse_mode='md')
        
        # Auto-delete in groups if enabled
        if not event.is_private and settings.AUTO_DELETE_COMMANDS:
            await asyncio.sleep(settings.COMMAND_DELETE_DELAY)
            try:
                await event.delete()
            except Exception as e:
                logger.error(f"Error deleting admin command: {e}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def ban_command(event):
        """Handle /ban command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
            
            # Extract reason and time if provided
            reason = None
            ban_time = None
            
            if len(args) > 1:
                # Check if the first argument is a time
                if helpers.is_time_format(args[1]):
                    ban_time = helpers.parse_time(args[1])
                    if len(args) > 2:
                        reason = " ".join(args[2:])
                else:
                    reason = " ".join(args[1:])
        else:
            # Extract user ID, reason, and time if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /ban <reply> [time] [reason] or /ban @username [time] [reason]")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
                    
                # Extract reason and time if provided
                reason = None
                ban_time = None
                
                if len(args) > 2:
                    # Check if the second argument is a time
                    if helpers.is_time_format(args[2]):
                        ban_time = helpers.parse_time(args[2])
                        if len(args) > 3:
                            reason = " ".join(args[3:])
                    else:
                        reason = " ".join(args[2:])
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /ban <reply> [time] [reason] or /ban @username [time] [reason]")
                return
        
        # Check if target user is an admin
        if await permissions.is_user_admin(client.client, chat.id, target_user.id):
            await event.reply("❌ I can't ban an admin.")
            return
            
        # Ban the user
        try:
            await client.client.edit_permissions(
                chat,
                target_user.id,
                view_messages=False,
                until_date=ban_time
            )
            
            # Format reason and time text
            reason_text = f" for: {reason}" if reason else ""
            time_text = f" for {helpers.format_time_duration(ban_time)}" if ban_time else " permanently"
            
            # Send ban message
            ban_message = messages.BAN_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user),
                reason_text=reason_text,
                time_text=time_text
            )
            
            await event.reply(ban_message, parse_mode='md')
            
            # Add ban to database
            db.add_ban(
                user_id=target_user.id,
                group_id=chat.id,
                admin_id=user.id,
                reason=reason,
                until_date=ban_time
            )
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="ban",
                details=f"Reason: {reason}, Time: {ban_time}"
            )
            
            # Notify admins
            admin_notification = f"🚫 **User Banned**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}\nReason: {reason or 'None'}\nDuration: {helpers.format_time_duration(ban_time) if ban_time else 'Permanent'}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await event.reply(f"❌ Failed to ban user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def unban_command(event):
        """Handle /unban command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Extract user ID
        if len(args) < 2:
            await event.reply("❌ No user specified. Use /unban @username or /unban user_id")
            return
            
        try:
            if args[1].startswith('@'):
                target_user = await client.client.get_entity(args[1])
            else:
                target_user = await client.client.get_entity(int(args[1]))
        except ValueError:
            await event.reply("❌ Invalid user specified. Use /unban @username or /unban user_id")
            return
            
        # Unban the user
        try:
            await client.client.edit_permissions(
                chat,
                target_user.id,
                view_messages=True
            )
            
            # Send unban message
            unban_message = messages.UNBAN_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user)
            )
            
            await event.reply(unban_message, parse_mode='md')
            
            # Update ban in database
            db.remove_ban(
                user_id=target_user.id,
                group_id=chat.id
            )
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="unban",
                details=None
            )
            
            # Notify admins
            admin_notification = f"✅ **User Unbanned**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await event.reply(f"❌ Failed to unban user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def kick_command(event):
        """Handle /kick command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
            
            # Extract reason if provided
            reason = None
            if len(args) > 1:
                reason = " ".join(args[1:])
        else:
            # Extract user ID and reason if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /kick <reply> [reason] or /kick @username [reason]")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
                    
                # Extract reason if provided
                reason = None
                if len(args) > 2:
                    reason = " ".join(args[2:])
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /kick <reply> [reason] or /kick @username [reason]")
                return
        
        # Check if target user is an admin
        if await permissions.is_user_admin(client.client, chat.id, target_user.id):
            await event.reply("❌ I can't kick an admin.")
            return
            
        # Kick the user
        try:
            # Ban and then unban to kick
            await client.client.edit_permissions(
                chat,
                target_user.id,
                view_messages=False
            )
            
            await client.client.edit_permissions(
                chat,
                target_user.id,
                view_messages=True
            )
            
            # Format reason text
            reason_text = f" for: {reason}" if reason else ""
            
            # Send kick message
            kick_message = messages.KICK_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user),
                reason_text=reason_text
            )
            
            await event.reply(kick_message, parse_mode='md')
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="kick",
                details=f"Reason: {reason}"
            )
            
            # Remove user from group in database
            db.remove_user_from_group(
                user_id=target_user.id,
                group_id=chat.id
            )
            
            # Notify admins
            admin_notification = f"👢 **User Kicked**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}\nReason: {reason or 'None'}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error kicking user: {e}")
            await event.reply(f"❌ Failed to kick user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def mute_command(event):
        """Handle /mute command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
            
            # Extract reason and time if provided
            reason = None
            mute_time = None
            
            if len(args) > 1:
                # Check if the first argument is a time
                if helpers.is_time_format(args[1]):
                    mute_time = helpers.parse_time(args[1])
                    if len(args) > 2:
                        reason = " ".join(args[2:])
                else:
                    reason = " ".join(args[1:])
        else:
            # Extract user ID, reason, and time if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /mute <reply> [time] [reason] or /mute @username [time] [reason]")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
                    
                # Extract reason and time if provided
                reason = None
                mute_time = None
                
                if len(args) > 2:
                    # Check if the second argument is a time
                    if helpers.is_time_format(args[2]):
                        mute_time = helpers.parse_time(args[2])
                        if len(args) > 3:
                            reason = " ".join(args[3:])
                    else:
                        reason = " ".join(args[2:])
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /mute <reply> [time] [reason] or /mute @username [time] [reason]")
                return
        
        # Check if target user is an admin
        if await permissions.is_user_admin(client.client, chat.id, target_user.id):
            await event.reply("❌ I can't mute an admin.")
            return
            
        # Mute the user
        try:
            await client.client.edit_permissions(
                chat,
                target_user.id,
                send_messages=False,
                until_date=mute_time
            )
            
            # Format reason and time text
            reason_text = f" for: {reason}" if reason else ""
            time_text = f" for {helpers.format_time_duration(mute_time)}" if mute_time else " indefinitely"
            
            # Send mute message
            mute_message = messages.MUTE_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user),
                reason_text=reason_text,
                time_text=time_text
            )
            
            await event.reply(mute_message, parse_mode='md')
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="mute",
                details=f"Reason: {reason}, Time: {mute_time}"
            )
            
            # Notify admins
            admin_notification = f"🔇 **User Muted**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}\nReason: {reason or 'None'}\nDuration: {helpers.format_time_duration(mute_time) if mute_time else 'Indefinite'}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error muting user: {e}")
            await event.reply(f"❌ Failed to mute user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def unmute_command(event):
        """Handle /unmute command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
        else:
            # Extract user ID if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /unmute <reply> or /unmute @username")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /unmute <reply> or /unmute @username")
                return
            
        # Unmute the user
        try:
            await client.client.edit_permissions(
                chat,
                target_user.id,
                send_messages=True
            )
            
            # Send unmute message
            unmute_message = messages.UNMUTE_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user)
            )
            
            await event.reply(unmute_message, parse_mode='md')
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="unmute",
                details=None
            )
            
            # Notify admins
            admin_notification = f"🔊 **User Unmuted**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error unmuting user: {e}")
            await event.reply(f"❌ Failed to unmute user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def warn_command(event):
        """Handle /warn command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
            
            # Extract reason if provided
            reason = None
            if len(args) > 1:
                reason = " ".join(args[1:])
        else:
            # Extract user ID and reason if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /warn <reply> [reason] or /warn @username [reason]")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
                    
                # Extract reason if provided
                reason = None
                if len(args) > 2:
                    reason = " ".join(args[2:])
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /warn <reply> [reason] or /warn @username [reason]")
                return
        
        # Check if target user is an admin
        if await permissions.is_user_admin(client.client, chat.id, target_user.id):
            await event.reply("❌ I can't warn an admin.")
            return
            
        # Add warning to database
        try:
            # Get group settings
            group_settings = db.get_group_settings(chat.id)
            warn_limit = group_settings.warning_threshold if group_settings else settings.DEFAULT_WARNING_THRESHOLD
            
            # Add warning
            warn_count = db.add_warning(
                user_id=target_user.id,
                group_id=chat.id,
                admin_id=user.id,
                reason=reason
            )
            
            # Format reason text
            reason_text = f" for: {reason}" if reason else ""
            
            # Send warn message
            warn_message = messages.WARN_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user),
                reason_text=reason_text,
                warn_count=warn_count,
                warn_limit=warn_limit
            )
            
            await event.reply(warn_message, parse_mode='md')
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="warn",
                details=f"Reason: {reason}, Count: {warn_count}/{warn_limit}"
            )
            
            # Check if warn limit reached
            if warn_count >= warn_limit:
                # Ban the user
                await client.client.edit_permissions(
                    chat,
                    target_user.id,
                    view_messages=False
                )
                
                # Send ban message
                ban_message = f"🚫 {helpers.get_user_link(target_user)} has been banned after receiving {warn_count} warnings."
                await event.reply(ban_message, parse_mode='md')
                
                # Add ban to database
                db.add_ban(
                    user_id=target_user.id,
                    group_id=chat.id,
                    admin_id=user.id,
                    reason=f"Exceeded warning limit ({warn_count}/{warn_limit})",
                    until_date=None
                )
                
                # Log the ban
                db.add_log(
                    group_id=chat.id,
                    user_id=target_user.id,
                    admin_id=user.id,
                    action="ban",
                    details=f"Reason: Exceeded warning limit ({warn_count}/{warn_limit})"
                )
                
                # Notify admins
                admin_notification = f"🚫 **User Auto-Banned**\n\nGroup: {chat.title}\nUser: {helpers.get_user_link(target_user)}\nReason: Exceeded warning limit ({warn_count}/{warn_limit})"
                await client.send_admin_notification(admin_notification)
            
            # Notify admins about the warning
            admin_notification = f"⚠️ **User Warned**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}\nReason: {reason or 'None'}\nWarnings: {warn_count}/{warn_limit}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error warning user: {e}")
            await event.reply(f"❌ Failed to warn user: {str(e)}")
    
    @decorators.handle_errors
    @decorators.log_command
    @decorators.admin_only
    async def unwarn_command(event):
        """Handle /unwarn command."""
        # Get user information
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
        
        # Parse command arguments
        args = event.text.split()
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
        else:
            # Extract user ID if provided
            if len(args) < 2:
                await event.reply("❌ No user specified. Use /unwarn <reply> or /unwarn @username")
                return
                
            try:
                if args[1].startswith('@'):
                    target_user = await client.client.get_entity(args[1])
                else:
                    target_user = await client.client.get_entity(int(args[1]))
            except ValueError:
                await event.reply("❌ Invalid user specified. Use /unwarn <reply> or /unwarn @username")
                return
            
        # Remove warning from database
        try:
            # Get group settings
            group_settings = db.get_group_settings(chat.id)
            warn_limit = group_settings.warning_threshold if group_settings else settings.DEFAULT_WARNING_THRESHOLD
            
            # Remove warning
            warn_count = db.remove_warning(
                user_id=target_user.id,
                group_id=chat.id
            )
            
            # Send unwarn message
            unwarn_message = messages.UNWARN_MESSAGE.format(
                admin=helpers.get_user_link(user),
                user_mention=helpers.get_user_link(target_user),
                warn_count=warn_count,
                warn_limit=warn_limit
            )
            
            await event.reply(unwarn_message, parse_mode='md')
            
            # Log the action
            db.add_log(
                group_id=chat.id,
                user_id=target_user.id,
                admin_id=user.id,
                action="unwarn",
                details=f"Count: {warn_count}/{warn_limit}"
            )
            
            # Notify admins
            admin_notification = f"✅ **Warning Removed**\n\nGroup: {chat.title}\nAdmin: {helpers.get_user_link(user)}\nUser: {helpers.get_user_link(target_user)}\nWarnings: {warn_count}/{warn_limit}"
            await client.send_admin_notification(admin_notification)
            
        except Exception as e:
            logger.error(f"Error removing warning: {e}")
            await event.reply(f"❌ Failed to remove warning: {str(e)}")
    
    # Register the event handlers
    client.client.add_event_handler(admin_command, events.NewMessage(pattern=r"^/admin(?:@\w+)?"))
    client.client.add_event_handler(ban_command, events.NewMessage(pattern=r"^/ban(?:@\w+)?"))
    client.client.add_event_handler(unban_command, events.NewMessage(pattern=r"^/unban(?:@\w+)?"))
    client.client.add_event_handler(kick_command, events.NewMessage(pattern=r"^/kick(?:@\w+)?"))
    client.client.add_event_handler(mute_command, events.NewMessage(pattern=r"^/mute(?:@\w+)?"))
    client.client.add_event_handler(unmute_command, events.NewMessage(pattern=r"^/unmute(?:@\w+)?"))
    client.client.add_event_handler(warn_command, events.NewMessage(pattern=r"^/warn(?:@\w+)?"))
    client.client.add_event_handler(unwarn_command, events.NewMessage(pattern=r"^/unwarn(?:@\w+)?"))