from telethon import events, Button
import asyncio

from telegram_protect_bot.config import settings, messages
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, decorators

async def setup(client):
    """Set up user command handlers."""
    
    from telethon import events
    
    @decorators.handle_errors
    @decorators.log_command
    async def start_command(event):
        """Handle /start command."""
        # Get user information
        user = await event.get_sender()
        
        # Update database
        db.get_or_create_user(
            user.id,
            user.first_name,
            user.last_name,
            user.username,
            getattr(user, 'bot', False)
        )
        
        # Format start message
        if event.is_private:
            # In private chat, show the main menu
            start_message = messages.MAIN_MENU_TEXT.format(
                user_name=user.first_name
            )
            
            # Create inline buttons for main menu
            buttons = [
                [
                    Button.url("➕ Add to Group", f"https://t.me/{settings.BOT_USERNAME}?startgroup=true"),
                    Button.callback("📊 Statistics", "analytics:main")
                ],
                [
                    Button.callback("⚙️ Settings", "settings:main"),
                    Button.callback("❓ Help & Support", "help_menu")
                ],
                [
                    Button.callback("📱 My Groups", "user_info:groups"),
                    Button.url("🔗 Official Channel", f"https://t.me/{settings.OWNER_USERNAME}")
                ],
                [
                    Button.callback("🌐 Language", "language:select"),
                    Button.callback("📋 About Bot", "about:bot")
                ]
            ]
        else:
            # In group chat, show simpler message
            start_message = messages.START_MESSAGE.format(
                mention=helpers.get_user_link(user),
                bot_name=settings.BOT_NAME
            )
            
            # Create simpler buttons for group chat
            buttons = [
                [Button.url("➕ Add to Group", f"https://t.me/{settings.BOT_USERNAME}?startgroup=true")],
                [Button.callback("⚙️ Settings", "settings:main"), Button.callback("❓ Help", "help_menu")]
            ]
        
        # Send message with buttons
        await event.reply(start_message, buttons=buttons, parse_mode='md')
    
    @decorators.handle_errors
    @decorators.log_command
    async def help_command(event):
        """Handle /help command."""
        # Format help message with interactive buttons
        help_message = messages.HELP_MENU_TEXT
        
        # Create help menu buttons
        buttons = [
            [
                Button.callback("👮 Admin Commands", "help:admin"),
                Button.callback("🛡️ Protection Features", "help:protection")
            ],
            [
                Button.callback("⚙️ Group Settings", "help:settings"),
                Button.callback("📊 Analytics & Reports", "help:analytics")
            ],
            [
                Button.callback("🤖 AI Features", "help:ai"),
                Button.callback("🔧 Troubleshooting", "help:troubleshooting")
            ],
            [
                Button.url("📞 Contact Support", f"https://t.me/{settings.OWNER_USERNAME}"),
                Button.callback("🆕 What's New", "help:whatsnew")
            ],
            [
                Button.callback("⬅️ Back to Main Menu", "main_menu")
            ]
        ]
        
        # Send help message with buttons
        await event.reply(help_message, buttons=buttons, parse_mode='md')
        
        # Auto-delete in groups if enabled
        if not event.is_private and settings.AUTO_DELETE_COMMANDS:
            await asyncio.sleep(settings.COMMAND_DELETE_DELAY)
            try:
                await event.delete()
            except Exception as e:
                print(f"Error deleting help command: {e}")
    
    @decorators.handle_errors
    @decorators.log_command
    async def info_command(event):
        """Handle /info command."""
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            user = await replied_msg.get_sender()
        else:
            # Extract user ID if provided
            args = event.text.split()
            if len(args) > 1:
                try:
                    if args[1].startswith('@'):
                        user = await client.client.get_entity(args[1])
                    else:
                        user = await client.client.get_entity(int(args[1]))
                except ValueError:
                    user = await event.get_sender()
            else:
                user = await event.get_sender()
                
        # Get chat information
        chat = await event.get_chat()
        
        # Update database
        db.get_or_create_user(
            user.id,
            user.first_name,
            user.last_name,
            user.username,
            getattr(user, 'bot', False)
        )
        
        if not event.is_private:
            db.get_or_create_group(chat.id, chat.title, getattr(chat, 'username', None))
            
        # Get user status
        user_status = "Admin" if await permissions.is_user_admin(client.client, chat.id, user.id) else "Member"
        if user.id == settings.OWNER_ID:
            user_status = "Owner"
        elif user.id in settings.SUDO_USERS:
            user_status = "Sudo User"
        elif user.id in settings.ADMIN_IDS:
            user_status = "Bot Admin"
            
        # Get member count for groups
        member_count = 1
        if not event.is_private:
            member_count = await helpers.get_chat_member_count(client.client, chat.id)
            
        # Format info message
        info_message = messages.INFO_MESSAGE.format(
            user_mention=helpers.get_user_link(user),
            user_id=user.id,
            username=user.username or "None",
            first_name=user.first_name or "None",
            last_name=user.last_name or "None",
            user_status=user_status,
            chat_title=chat.title if not event.is_private else "Private Chat",
            chat_id=chat.id,
            chat_type=chat.stringify() if not event.is_private else "Private",
            member_count=member_count,
            created_date=user.date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(user, 'date') else "Unknown"
        )
        
        # Send info message
        await event.reply(info_message, parse_mode='md')
        
        # Auto-delete in groups if enabled
        if not event.is_private and settings.AUTO_DELETE_COMMANDS:
            await asyncio.sleep(settings.COMMAND_DELETE_DELAY)
            try:
                await event.delete()
            except Exception as e:
                print(f"Error deleting info command: {e}")
    
    @decorators.handle_errors
    @decorators.log_command
    async def rules_command(event):
        """Handle /rules command."""
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
            
        # Get chat information
        chat_id = event.chat_id
        chat = await event.get_chat()
        
        # Get group settings
        group_settings = db.get_group_settings(chat_id)
        
        if not group_settings or not group_settings.rules:
            rules_text = settings.DEFAULT_RULES_MESSAGE
        else:
            rules_text = group_settings.rules
            
        # Format rules message
        rules_message = messages.RULES_MESSAGE.format(
            rules_text=rules_text
        )
        
        # Send rules message
        await event.reply(rules_message, parse_mode='md')
        
        # Auto-delete if enabled
        if settings.AUTO_DELETE_COMMANDS:
            await asyncio.sleep(settings.COMMAND_DELETE_DELAY)
            try:
                await event.delete()
            except Exception as e:
                print(f"Error deleting rules command: {e}")
    
    @decorators.handle_errors
    @decorators.log_command
    async def report_command(event):
        """Handle /report command."""
        # Skip in private chats
        if event.is_private:
            await event.reply("❌ This command can only be used in groups.")
            return
            
        # Get chat and user information
        chat_id = event.chat_id
        chat = await event.get_chat()
        user = await event.get_sender()
        
        # Extract reported user and reason
        reported_user = None
        reason = None
        
        # Check if command is a reply
        if event.reply_to:
            replied_msg = await event.get_reply_message()
            reported_user = await replied_msg.get_sender()
            
            # Extract reason if provided
            args = event.text.split(None, 1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Extract user ID and reason if provided
            args = event.text.split(None, 2)
            if len(args) > 1:
                try:
                    if args[1].startswith('@'):
                        reported_user = await client.client.get_entity(args[1])
                    else:
                        reported_user = await client.client.get_entity(int(args[1]))
                        
                    if len(args) > 2:
                        reason = args[2]
                except ValueError:
                    await event.reply("❌ Invalid user specified. Use /report <reply> [reason] or /report @username [reason]")
                    return
            else:
                await event.reply("❌ No user specified. Use /report <reply> [reason] or /report @username [reason]")
                return
                
        if not reported_user:
            await event.reply("❌ Could not identify the user to report.")
            return
            
        # Format reason text
        reason_text = f"\nReason: {reason}" if reason else ""
        
        # Get admins
        admin_ids = await permissions.get_chat_admins(client.client, chat_id)
        
        # Send report message
        report_message = f"⚠️ **Report from {helpers.get_user_link(user)}**\n\nReported user: {helpers.get_user_link(reported_user)}{reason_text}"
        report_msg = await event.reply(report_message, parse_mode='md')
        
        # Notify admins
        admin_notification = f"⚠️ **New Report in {chat.title}**\n\nFrom: {helpers.get_user_link(user)}\nReported user: {helpers.get_user_link(reported_user)}{reason_text}"
        await client.send_message_to_log_channel(admin_notification)
        
        # Log the report
        db.add_log(
            action="report",
            group_id=chat_id,
            user_id=reported_user.id,
            admin_id=user.id,
            details=f"Reporter: {user.id}, Reason: {reason}"
        )
        
        # Thank the reporter
        await event.reply("✅ Thank you for your report. Admins have been notified.")
    
    # Register the event handlers
    client.client.add_event_handler(start_command, events.NewMessage(pattern=r"^/start(?:@\w+)?"))
    client.client.add_event_handler(help_command, events.NewMessage(pattern=r"^/help(?:@\w+)?"))
    client.client.add_event_handler(info_command, events.NewMessage(pattern=r"^/info(?:@\w+)?"))
    client.client.add_event_handler(rules_command, events.NewMessage(pattern=r"^/rules(?:@\w+)?"))
    client.client.add_event_handler(report_command, events.NewMessage(pattern=r"^/report(?:@\w+)?"))