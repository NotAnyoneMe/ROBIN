from telethon import events, Button
import asyncio

from telegram_protect_bot.config import settings, messages
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, permissions, decorators

async def setup(client):
    """Set up settings command handlers."""
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def settings_command(event):
        """Handle /settings command."""
        # Get chat information
        chat_id = event.chat_id
        
        # Get group settings
        group_settings = db.get_group_settings(chat_id)
        if not group_settings:
            await event.reply("❌ Group settings not found. Please try again later.")
            return
            
        # Format settings message
        settings_message = messages.SETTINGS_MESSAGE.format(
            antispam_status="✅ Enabled" if group_settings.antispam_enabled else "❌ Disabled",
            link_filtering_status="✅ Enabled" if group_settings.link_filtering_enabled else "❌ Disabled",
            media_filtering_status="✅ Enabled" if group_settings.media_filtering_enabled else "❌ Disabled",
            welcome_messages_status="✅ Enabled" if group_settings.welcome_enabled else "❌ Disabled",
            goodbye_messages_status="✅ Enabled" if group_settings.goodbye_enabled else "❌ Disabled",
            auto_delete_commands_status="✅ Enabled" if group_settings.auto_delete_commands else "❌ Disabled"
        )
        
        # Create settings buttons
        buttons = [
            [
                Button.inline("Anti-Spam", f"setting_antispam_{chat_id}"),
                Button.inline("Link Filter", f"setting_link_{chat_id}")
            ],
            [
                Button.inline("Media Filter", f"setting_media_{chat_id}"),
                Button.inline("Welcome Msgs", f"setting_welcome_{chat_id}")
            ],
            [
                Button.inline("Goodbye Msgs", f"setting_goodbye_{chat_id}"),
                Button.inline("Auto-Delete", f"setting_autodelete_{chat_id}")
            ],
            [
                Button.inline("Close", f"setting_close_{chat_id}")
            ]
        ]
        
        # Send settings message with buttons
        await event.reply(settings_message, buttons=buttons, parse_mode='md')
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def welcome_command(event):
        """Handle /welcome command."""
        # Get chat information
        chat_id = event.chat_id
        
        # Extract welcome message
        args = event.text.split(None, 1)
        
        if len(args) > 1:
            welcome_message = args[1]
            
            # Update welcome message in database
            db.update_group_settings(chat_id, welcome_message=welcome_message)
            
            # Send confirmation
            await event.reply("✅ Welcome message updated successfully!\n\nPreview:\n" + welcome_message)
        else:
            # Get current welcome message
            group_settings = db.get_group_settings(chat_id)
            
            if not group_settings:
                await event.reply("❌ Group settings not found. Please try again later.")
                return
                
            current_message = group_settings.welcome_message or settings.DEFAULT_WELCOME_MESSAGE
            
            # Send current welcome message and instructions
            await event.reply(f"Current welcome message:\n\n{current_message}\n\nTo update, use /welcome <new message>\n\nAvailable variables: {{mention}}, {{first_name}}, {{last_name}}, {{username}}, {{user_id}}, {{chat_title}}, {{chat_id}}")
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def goodbye_command(event):
        """Handle /goodbye command."""
        # Get chat information
        chat_id = event.chat_id
        
        # Extract goodbye message
        args = event.text.split(None, 1)
        
        if len(args) > 1:
            goodbye_message = args[1]
            
            # Update goodbye message in database
            db.update_group_settings(chat_id, goodbye_message=goodbye_message)
            
            # Send confirmation
            await event.reply("✅ Goodbye message updated successfully!\n\nPreview:\n" + goodbye_message)
        else:
            # Get current goodbye message
            group_settings = db.get_group_settings(chat_id)
            
            if not group_settings:
                await event.reply("❌ Group settings not found. Please try again later.")
                return
                
            current_message = group_settings.goodbye_message or settings.DEFAULT_GOODBYE_MESSAGE
            
            # Send current goodbye message and instructions
            await event.reply(f"Current goodbye message:\n\n{current_message}\n\nTo update, use /goodbye <new message>\n\nAvailable variables: {{mention}}, {{first_name}}, {{last_name}}, {{username}}, {{user_id}}, {{chat_title}}, {{chat_id}}")
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def rules_command(event):
        """Handle /rules command for setting rules."""
        # Get chat information
        chat_id = event.chat_id
        
        # Extract rules text
        args = event.text.split(None, 1)
        
        if len(args) > 1:
            rules_text = args[1]
            
            # Update rules in database
            db.update_group_settings(chat_id, rules=rules_text)
            
            # Send confirmation
            await event.reply("✅ Group rules updated successfully!")
        else:
            # Get current rules
            group_settings = db.get_group_settings(chat_id)
            
            if not group_settings:
                await event.reply("❌ Group settings not found. Please try again later.")
                return
                
            current_rules = group_settings.rules or settings.DEFAULT_RULES_MESSAGE
            
            # Send current rules and instructions
            await event.reply(f"Current group rules:\n\n{current_rules}\n\nTo update, use /rules <new rules>")
    
    @client.add_event_handler
    @decorators.admin_required
    @decorators.group_only
    @decorators.handle_errors
    @decorators.log_command
    async def antispam_command(event):
        """Handle /antispam command."""
        # Get chat information
        chat_id = event.chat_id
        
        # Extract setting
        args = event.text.split()
        
        if len(args) > 1:
            setting = args[1].lower()
            
            if setting in ['on', 'yes', 'true', 'enable', 'enabled']:
                enabled = True
            elif setting in ['off', 'no', 'false', 'disable', 'disabled']:
                enabled = False
            else:
                await event.reply("❌ Invalid option. Use 'on' or 'off'.")
                return
                
            # Update antispam setting in database
            db.update_group_settings(chat_id, antispam_enabled=enabled)
            
            # Send confirmation
            status = "enabled" if enabled else "disabled"
            await event.reply(f"✅ Anti-spam system {status} successfully!")
        else:
            # Get current setting
            group_settings = db.get_group_settings(chat_id)
            
            if not group_settings:
                await event.reply("❌ Group settings not found. Please try again later.")
                return
                
            current_setting = "enabled" if group_settings.antispam_enabled else "disabled"
            
            # Send current setting and instructions
            await event.reply(f"Anti-spam system is currently {current_setting}.\n\nTo change, use /antispam on or /antispam off")
    
    @client.add_event_handler
    async def callback_query_handler(event):
        """Handle callback queries for settings buttons."""
        # Get the data
        data = event.data.decode('utf-8')
        
        # Check if it's a settings callback
        if not data.startswith('setting_'):
            return
            
        # Extract setting type and chat ID
        parts = data.split('_')
        if len(parts) < 3:
            return
            
        setting_type = parts[1]
        chat_id = int(parts[2])
        
        # Check if user is an admin
        user_id = event.sender_id
        is_admin = await permissions.is_user_admin(client.client, chat_id, user_id)
        
        if not is_admin and not permissions.is_admin_user(user_id):
            await event.answer("❌ You must be an admin to change settings.", alert=True)
            return
            
        # Get group settings
        group_settings = db.get_group_settings(chat_id)
        if not group_settings:
            await event.answer("❌ Group settings not found. Please try again later.", alert=True)
            return
            
        # Handle different setting types
        if setting_type == 'close':
            # Delete the message
            await event.delete()
            return
            
        elif setting_type == 'antispam':
            # Toggle antispam setting
            new_value = not group_settings.antispam_enabled
            db.update_group_settings(chat_id, antispam_enabled=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Anti-spam system {status} successfully!")
            
        elif setting_type == 'link':
            # Toggle link filtering setting
            new_value = not group_settings.link_filtering_enabled
            db.update_group_settings(chat_id, link_filtering_enabled=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Link filtering {status} successfully!")
            
        elif setting_type == 'media':
            # Toggle media filtering setting
            new_value = not group_settings.media_filtering_enabled
            db.update_group_settings(chat_id, media_filtering_enabled=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Media filtering {status} successfully!")
            
        elif setting_type == 'welcome':
            # Toggle welcome messages setting
            new_value = not group_settings.welcome_enabled
            db.update_group_settings(chat_id, welcome_enabled=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Welcome messages {status} successfully!")
            
        elif setting_type == 'goodbye':
            # Toggle goodbye messages setting
            new_value = not group_settings.goodbye_enabled
            db.update_group_settings(chat_id, goodbye_enabled=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Goodbye messages {status} successfully!")
            
        elif setting_type == 'autodelete':
            # Toggle auto-delete commands setting
            new_value = not group_settings.auto_delete_commands
            db.update_group_settings(chat_id, auto_delete_commands=new_value)
            status = "enabled" if new_value else "disabled"
            await event.answer(f"Auto-delete commands {status} successfully!")
            
        # Update the settings message
        try:
            # Get updated settings
            updated_settings = db.get_group_settings(chat_id)
            
            # Format updated settings message
            settings_message = messages.SETTINGS_MESSAGE.format(
                antispam_status="✅ Enabled" if updated_settings.antispam_enabled else "❌ Disabled",
                link_filtering_status="✅ Enabled" if updated_settings.link_filtering_enabled else "❌ Disabled",
                media_filtering_status="✅ Enabled" if updated_settings.media_filtering_enabled else "❌ Disabled",
                welcome_messages_status="✅ Enabled" if updated_settings.welcome_enabled else "❌ Disabled",
                goodbye_messages_status="✅ Enabled" if updated_settings.goodbye_enabled else "❌ Disabled",
                auto_delete_commands_status="✅ Enabled" if updated_settings.auto_delete_commands else "❌ Disabled"
            )
            
            # Update the message
            await event.edit(settings_message, buttons=[
                [
                    Button.inline("Anti-Spam", f"setting_antispam_{chat_id}"),
                    Button.inline("Link Filter", f"setting_link_{chat_id}")
                ],
                [
                    Button.inline("Media Filter", f"setting_media_{chat_id}"),
                    Button.inline("Welcome Msgs", f"setting_welcome_{chat_id}")
                ],
                [
                    Button.inline("Goodbye Msgs", f"setting_goodbye_{chat_id}"),
                    Button.inline("Auto-Delete", f"setting_autodelete_{chat_id}")
                ],
                [
                    Button.inline("Close", f"setting_close_{chat_id}")
                ]
            ], parse_mode='md')
        except Exception as e:
            print(f"Error updating settings message: {e}")
    
    # Register the event handlers
    client.add_event_handler(settings_command, events.NewMessage(pattern=r"^/settings(?:@\w+)?"))
    client.add_event_handler(welcome_command, events.NewMessage(pattern=r"^/welcome(?:@\w+)?"))
    client.add_event_handler(goodbye_command, events.NewMessage(pattern=r"^/goodbye(?:@\w+)?"))
    client.add_event_handler(rules_command, events.NewMessage(pattern=r"^/setrules(?:@\w+)?"))
    client.add_event_handler(antispam_command, events.NewMessage(pattern=r"^/antispam(?:@\w+)?"))
    client.add_event_handler(callback_query_handler, events.CallbackQuery())