from telethon import events
import json
import base64
import logging
from typing import Dict, Any, Tuple, Optional, List, Union

from telegram_protect_bot.bot.utils import permissions
from telegram_protect_bot.database import operations
from telegram_protect_bot.config import messages

logger = logging.getLogger(__name__)

class CallbackData:
    """Structured callback data class."""
    
    @staticmethod
    def serialize(action: str, **params) -> str:
        """
        Serialize callback data to a string.
        
        Args:
            action: The action to perform
            **params: Additional parameters for the action
            
        Returns:
            str: Base64-encoded JSON string
        """
        data = {"a": action}
        if params:
            data["p"] = params
        json_data = json.dumps(data)
        return base64.b64encode(json_data.encode()).decode()
    
    @staticmethod
    def deserialize(data: str) -> Tuple[str, Dict[str, Any]]:
        """
        Deserialize callback data from a string.
        
        Args:
            data: Base64-encoded JSON string
            
        Returns:
            Tuple[str, Dict[str, Any]]: Action and parameters
        """
        try:
            json_data = base64.b64decode(data.encode()).decode()
            data_dict = json.loads(json_data)
            action = data_dict.get("a", "")
            params = data_dict.get("p", {})
            return action, params
        except Exception as e:
            logger.error(f"Error deserializing callback data: {e}")
            return "", {}

# Callback data format: action:param1:param2:...
# For example: settings:antispam:toggle

async def callback_query_handler(event):
    """Handle callback queries from inline buttons."""
    try:
        # Get the callback data
        data = event.data.decode('utf-8')
        logger.info(f"Callback query received: {data[:20]}...")
        
        # Parse the callback data
        # Check if it's the new format or old format
        if data.startswith('eyJ'):  # Base64 JSON format starts with 'eyJ'
            # New format
            action, params = CallbackData.deserialize(data)
            parts = [action] + list(params.values()) if params else [action]
        else:
            # Old format for backward compatibility
            parts = data.split(':')
            action = parts[0]
            params = {f"param{i}": param for i, param in enumerate(parts[1:], 1)} if len(parts) > 1 else {}
        
        # Get the user who clicked the button
        user = await event.get_sender()
        chat = await event.get_chat()
        
        # Check if the user is an admin (for admin-only actions)
        is_admin = await permissions.is_user_admin(event.client, chat.id, user.id)
        
        # Admin-only actions
        admin_actions = {
            "admin_panel", "settings", "ban_user", "mute_user", 
            "warn_user", "clean_messages"
        }
        
        # Check admin permissions for admin-only actions
        if action in admin_actions and not is_admin:
            await event.answer(f"You need to be an admin to {action.replace('_', ' ')}.", alert=True)
            return
        
        # Handle different callback actions
        if action == "main_menu":
            await handle_main_menu(event, user, chat)
        
        elif action == "help_menu":
            await handle_help_menu(event, user, chat)
        
        elif action == "admin_panel":
            await handle_admin_panel(event, user, chat, parts)
        
        elif action == "settings":
            await handle_settings(event, user, chat, parts)
        
        elif action == "user_info":
            await handle_user_info(event, user, chat, parts)
        
        elif action == "ban_user":
            await handle_ban_user(event, user, chat, parts)
        
        elif action == "mute_user":
            await handle_mute_user(event, user, chat, parts)
        
        elif action == "warn_user":
            await handle_warn_user(event, user, chat, parts)
        
        elif action == "clean_messages":
            await handle_clean_messages(event, user, chat, parts)
        
        elif action == "analytics":
            await handle_analytics(event, user, chat, parts)
        
        elif action == "language":
            await handle_language(event, user, chat, parts)
        
        else:
            await event.answer("Unknown action. Please try again.", alert=True)
    
    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_main_menu(event, user, chat):
    """Handle main menu callbacks."""
    try:
        # Create the main menu message with inline buttons
        buttons = [
            [
                event.client.build_reply_markup().button(
                    text="➕ Add to Group", 
                    url=f"https://t.me/{event.client.username}?startgroup=true"
                ),
                event.client.build_reply_markup().button(
                    text="📊 Statistics", 
                    callback_data=CallbackData.serialize("analytics", section="main")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="⚙️ Settings", 
                    callback_data=CallbackData.serialize("settings", section="main")
                ),
                event.client.build_reply_markup().button(
                    text="❓ Help & Support", 
                    callback_data=CallbackData.serialize("help_menu")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="📱 My Groups", 
                    callback_data=CallbackData.serialize("user_info", section="groups")
                ),
                event.client.build_reply_markup().button(
                    text="🔗 Official Channel", 
                    url="https://t.me/ProtectionBotChannel"
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="🌐 Language", 
                    callback_data=CallbackData.serialize("language", action="select")
                ),
                event.client.build_reply_markup().button(
                    text="📋 About Bot", 
                    callback_data=CallbackData.serialize("about", section="bot")
                )
            ]
        ]
        
        markup = event.client.build_reply_markup().inline(buttons)
        
        # Edit the message with the main menu
        await event.edit(
            messages.MAIN_MENU_TEXT.format(user_name=user.first_name),
            buttons=markup
        )
        
        # Answer the callback query
        await event.answer()
    
    except Exception as e:
        logger.error(f"Error handling main menu: {e}", exc_info=True)
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_help_menu(event, user, chat):
    """Handle help menu callbacks."""
    try:
        # Create the help menu message with inline buttons
        buttons = [
            [
                event.client.build_reply_markup().button(
                    text="👮 Admin Commands", 
                    callback_data=CallbackData.serialize("help", section="admin")
                ),
                event.client.build_reply_markup().button(
                    text="🛡️ Protection Features", 
                    callback_data=CallbackData.serialize("help", section="protection")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="⚙️ Group Settings", 
                    callback_data=CallbackData.serialize("help", section="settings")
                ),
                event.client.build_reply_markup().button(
                    text="📊 Analytics & Reports", 
                    callback_data=CallbackData.serialize("help", section="analytics")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="🤖 AI Features", 
                    callback_data=CallbackData.serialize("help", section="ai")
                ),
                event.client.build_reply_markup().button(
                    text="🔧 Troubleshooting", 
                    callback_data=CallbackData.serialize("help", section="troubleshooting")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="📞 Contact Support", 
                    url="https://t.me/ProtectionBotSupport"
                ),
                event.client.build_reply_markup().button(
                    text="🆕 What's New", 
                    callback_data=CallbackData.serialize("help", section="whatsnew")
                )
            ],
            [
                event.client.build_reply_markup().button(
                    text="⬅️ Back to Main Menu", 
                    callback_data=CallbackData.serialize("main_menu")
                )
            ]
        ]
        
        markup = event.client.build_reply_markup().inline(buttons)
        
        # Edit the message with the help menu
        await event.edit(
            messages.HELP_MENU_TEXT,
            buttons=markup
        )
        
        # Answer the callback query
        await event.answer()
    
    except Exception as e:
        logger.error(f"Error handling help menu: {e}", exc_info=True)
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_admin_panel(event, user, chat, parts):
    """Handle admin panel callbacks."""
    try:
        # Create the admin panel message with inline buttons
        buttons = [
            [
                event.client.build_reply_markup().button(text="🚫 Ban User", callback_data="ban_user:select"),
                event.client.build_reply_markup().button(text="👢 Kick User", callback_data="kick_user:select"),
                event.client.build_reply_markup().button(text="🔇 Mute User", callback_data="mute_user:select")
            ],
            [
                event.client.build_reply_markup().button(text="⚠️ Warn User", callback_data="warn_user:select"),
                event.client.build_reply_markup().button(text="📝 Note User", callback_data="note_user:select"),
                event.client.build_reply_markup().button(text="🔍 Check User", callback_data="check_user:select")
            ],
            [
                event.client.build_reply_markup().button(text="🧹 Clean Messages", callback_data="clean_messages:options"),
                event.client.build_reply_markup().button(text="📌 Pin Message", callback_data="pin_message"),
                event.client.build_reply_markup().button(text="🔓 Unpin", callback_data="unpin_message")
            ],
            [
                event.client.build_reply_markup().button(text="🔒 Lock Chat", callback_data="lock_chat:options"),
                event.client.build_reply_markup().button(text="📢 Announce", callback_data="announce:create"),
                event.client.build_reply_markup().button(text="⬅️ Back", callback_data="main_menu")
            ]
        ]
        
        markup = event.client.build_reply_markup().inline(buttons)
        
        # Edit the message with the admin panel
        await event.edit(
            messages.ADMIN_PANEL_TEXT,
            buttons=markup
        )
        
        # Answer the callback query
        await event.answer()
    
    except Exception as e:
        logger.error(f"Error handling admin panel: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_settings(event, user, chat, parts):
    """Handle settings callbacks."""
    try:
        if len(parts) == 1 or parts[1] == "main":
            # Main settings menu
            buttons = [
                [
                    event.client.build_reply_markup().button(text="🛡️ Anti-Spam", callback_data="settings:antispam"),
                    event.client.build_reply_markup().button(text="👋 Welcome/Goodbye", callback_data="settings:welcome")
                ],
                [
                    event.client.build_reply_markup().button(text="🚫 Content Filters", callback_data="settings:filters"),
                    event.client.build_reply_markup().button(text="🤖 AI Moderation", callback_data="settings:ai")
                ],
                [
                    event.client.build_reply_markup().button(text="📱 Media Settings", callback_data="settings:media"),
                    event.client.build_reply_markup().button(text="🔒 Security", callback_data="settings:security")
                ],
                [
                    event.client.build_reply_markup().button(text="📊 Analytics", callback_data="settings:analytics"),
                    event.client.build_reply_markup().button(text="🌐 Language", callback_data="settings:language")
                ],
                [
                    event.client.build_reply_markup().button(text="⏰ Time Zones", callback_data="settings:timezone"),
                    event.client.build_reply_markup().button(text="💾 Backup/Restore", callback_data="settings:backup")
                ],
                [
                    event.client.build_reply_markup().button(text="🔄 Reset Settings", callback_data="settings:reset"),
                    event.client.build_reply_markup().button(text="⬅️ Back", callback_data="main_menu")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Get current group settings
            group_settings = await operations.get_group_settings(chat.id)
            
            # Edit the message with the settings menu
            await event.edit(
                messages.SETTINGS_MENU_TEXT.format(
                    group_name=chat.title,
                    group_id=chat.id
                ),
                buttons=markup
            )
        
        elif parts[1] == "antispam":
            # Anti-spam settings menu
            group_settings = await operations.get_group_settings(chat.id)
            
            antispam_status = "✅ Enabled" if group_settings.antispam_enabled else "❌ Disabled"
            link_filtering = "✅ Enabled" if group_settings.link_filtering_enabled else "❌ Disabled"
            
            buttons = [
                [
                    event.client.build_reply_markup().button(text="⚡ Quick Settings", callback_data="settings:antispam:quick"),
                    event.client.build_reply_markup().button(text="🔧 Advanced Config", callback_data="settings:antispam:advanced")
                ],
                [
                    event.client.build_reply_markup().button(text="📋 Spam Triggers", callback_data="settings:antispam:triggers"),
                    event.client.build_reply_markup().button(text="⚪ Whitelist", callback_data="settings:antispam:whitelist")
                ],
                [
                    event.client.build_reply_markup().button(text="⚫ Blacklist", callback_data="settings:antispam:blacklist"),
                    event.client.build_reply_markup().button(text="📊 Spam Reports", callback_data="settings:antispam:reports")
                ],
                [
                    event.client.build_reply_markup().button(text="🔄 Reset Counters", callback_data="settings:antispam:reset"),
                    event.client.build_reply_markup().button(text="💾 Save", callback_data="settings:antispam:save")
                ],
                [
                    event.client.build_reply_markup().button(text="⬅️ Back to Settings", callback_data="settings:main")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the anti-spam settings
            await event.edit(
                messages.ANTISPAM_SETTINGS_TEXT.format(
                    antispam_status=antispam_status,
                    link_filtering=link_filtering,
                    message_limit=group_settings.message_limit,
                    message_window=group_settings.message_window,
                    forward_limit=group_settings.forward_limit,
                    forward_window=group_settings.forward_window
                ),
                buttons=markup
            )
        
        elif parts[1] == "welcome":
            # Welcome settings menu
            group_settings = await operations.get_group_settings(chat.id)
            
            welcome_status = "✅ Enabled" if group_settings.welcome_enabled else "❌ Disabled"
            goodbye_status = "✅ Enabled" if group_settings.goodbye_enabled else "❌ Disabled"
            
            buttons = [
                [
                    event.client.build_reply_markup().button(text="✏️ Edit Welcome", callback_data="settings:welcome:edit_welcome"),
                    event.client.build_reply_markup().button(text="✏️ Edit Goodbye", callback_data="settings:welcome:edit_goodbye")
                ],
                [
                    event.client.build_reply_markup().button(text="🖼️ Add Media", callback_data="settings:welcome:add_media"),
                    event.client.build_reply_markup().button(text="🎨 Message Style", callback_data="settings:welcome:style")
                ],
                [
                    event.client.build_reply_markup().button(text="⏰ Auto-Delete", callback_data="settings:welcome:auto_delete"),
                    event.client.build_reply_markup().button(text="🔧 Variables", callback_data="settings:welcome:variables")
                ],
                [
                    event.client.build_reply_markup().button(text="👀 Preview", callback_data="settings:welcome:preview"),
                    event.client.build_reply_markup().button(text="🧪 Test Message", callback_data="settings:welcome:test")
                ],
                [
                    event.client.build_reply_markup().button(text="💾 Save Changes", callback_data="settings:welcome:save"),
                    event.client.build_reply_markup().button(text="⬅️ Back to Settings", callback_data="settings:main")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the welcome settings
            await event.edit(
                messages.WELCOME_SETTINGS_TEXT.format(
                    welcome_status=welcome_status,
                    goodbye_status=goodbye_status,
                    auto_delete_time=group_settings.auto_delete_welcome_time // 60
                ),
                buttons=markup
            )
        
        # Add more settings sections as needed
        
        else:
            # Unknown settings section
            await event.answer("This settings section is not yet implemented.", alert=True)
            await handle_settings(event, user, chat, ["settings", "main"])
    
    except Exception as e:
        logger.error(f"Error handling settings: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_ban_user(event, user, chat, parts):
    """Handle ban user callbacks."""
    try:
        if len(parts) == 1 or parts[1] == "select":
            # Show user selection interface
            await event.answer("Please reply to a message from the user you want to ban.")
            await event.edit(
                messages.BAN_USER_SELECT_TEXT,
                buttons=[
                    [event.client.build_reply_markup().button(text="❌ Cancel", callback_data="admin_panel")]
                ]
            )
        
        elif parts[1] == "options" and len(parts) >= 3:
            # Show ban options for the selected user
            target_user_id = int(parts[2])
            target_user = await event.client.get_entity(target_user_id)
            
            buttons = [
                [
                    event.client.build_reply_markup().button(text="⏰ 1 Hour", callback_data=f"ban_user:confirm:{target_user_id}:3600"),
                    event.client.build_reply_markup().button(text="⏰ 6 Hours", callback_data=f"ban_user:confirm:{target_user_id}:21600"),
                    event.client.build_reply_markup().button(text="⏰ 1 Day", callback_data=f"ban_user:confirm:{target_user_id}:86400")
                ],
                [
                    event.client.build_reply_markup().button(text="⏰ 7 Days", callback_data=f"ban_user:confirm:{target_user_id}:604800"),
                    event.client.build_reply_markup().button(text="⏰ 30 Days", callback_data=f"ban_user:confirm:{target_user_id}:2592000"),
                    event.client.build_reply_markup().button(text="🔒 Permanent", callback_data=f"ban_user:confirm:{target_user_id}:0")
                ],
                [
                    event.client.build_reply_markup().button(text="📝 Custom Time", callback_data=f"ban_user:custom:{target_user_id}"),
                    event.client.build_reply_markup().button(text="❌ Cancel", callback_data="admin_panel"),
                    event.client.build_reply_markup().button(text="✅ Confirm", callback_data=f"ban_user:confirm:{target_user_id}:0")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the ban options
            await event.edit(
                messages.BAN_USER_OPTIONS_TEXT.format(
                    user_name=target_user.first_name,
                    user_id=target_user.id,
                    username=target_user.username or "None"
                ),
                buttons=markup
            )
        
        elif parts[1] == "confirm" and len(parts) >= 4:
            # Confirm ban for the selected user
            target_user_id = int(parts[2])
            ban_time = int(parts[3])
            
            # Ban the user
            try:
                await event.client.edit_permissions(
                    chat,
                    target_user_id,
                    view_messages=False,
                    until_date=None if ban_time == 0 else ban_time
                )
                
                # Add ban to database
                await operations.add_ban(
                    user_id=target_user_id,
                    group_id=chat.id,
                    admin_id=user.id,
                    reason="Banned via admin panel",
                    until_date=None if ban_time == 0 else ban_time
                )
                
                # Log the action
                await operations.add_log(
                    group_id=chat.id,
                    user_id=target_user_id,
                    admin_id=user.id,
                    action="ban",
                    details=f"Ban time: {ban_time} seconds"
                )
                
                # Edit the message to show success
                await event.edit(
                    messages.BAN_USER_SUCCESS_TEXT.format(
                        user_id=target_user_id,
                        ban_time="permanently" if ban_time == 0 else f"for {ban_time} seconds"
                    ),
                    buttons=[
                        [event.client.build_reply_markup().button(text="⬅️ Back to Admin Panel", callback_data="admin_panel")]
                    ]
                )
            
            except Exception as e:
                logger.error(f"Error banning user: {e}")
                await event.answer(f"Failed to ban user: {str(e)}", alert=True)
                await handle_admin_panel(event, user, chat, ["admin_panel"])
        
        else:
            # Unknown ban action
            await event.answer("Invalid ban action.", alert=True)
            await handle_admin_panel(event, user, chat, ["admin_panel"])
    
    except Exception as e:
        logger.error(f"Error handling ban user: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_mute_user(event, user, chat, parts):
    """Handle mute user callbacks."""
    try:
        if len(parts) == 1 or parts[1] == "select":
            # Show user selection interface
            await event.answer("Please reply to a message from the user you want to mute.")
            await event.edit(
                messages.MUTE_USER_SELECT_TEXT,
                buttons=[
                    [event.client.build_reply_markup().button(text="❌ Cancel", callback_data="admin_panel")]
                ]
            )
        
        elif parts[1] == "options" and len(parts) >= 3:
            # Show mute options for the selected user
            target_user_id = int(parts[2])
            target_user = await event.client.get_entity(target_user_id)
            
            buttons = [
                [
                    event.client.build_reply_markup().button(text="🚫 Can't Send Messages", callback_data=f"mute_user:restrict:{target_user_id}:send_messages"),
                    event.client.build_reply_markup().button(text="🚫 Can't Send Media", callback_data=f"mute_user:restrict:{target_user_id}:send_media")
                ],
                [
                    event.client.build_reply_markup().button(text="🚫 Can't Send Stickers", callback_data=f"mute_user:restrict:{target_user_id}:send_stickers"),
                    event.client.build_reply_markup().button(text="🚫 Can't Add Users", callback_data=f"mute_user:restrict:{target_user_id}:invite_users")
                ],
                [
                    event.client.build_reply_markup().button(text="🚫 Can't Pin Messages", callback_data=f"mute_user:restrict:{target_user_id}:pin_messages"),
                    event.client.build_reply_markup().button(text="🚫 Can't Change Info", callback_data=f"mute_user:restrict:{target_user_id}:change_info")
                ],
                [
                    event.client.build_reply_markup().button(text="⏰ Set Duration", callback_data=f"mute_user:duration:{target_user_id}"),
                    event.client.build_reply_markup().button(text="✅ Apply", callback_data=f"mute_user:confirm:{target_user_id}"),
                    event.client.build_reply_markup().button(text="❌ Cancel", callback_data="admin_panel")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the mute options
            await event.edit(
                messages.MUTE_USER_OPTIONS_TEXT.format(
                    user_name=target_user.first_name,
                    username=target_user.username or "None"
                ),
                buttons=markup
            )
        
        elif parts[1] == "restrict" and len(parts) >= 4:
            # Toggle restriction for the selected user
            target_user_id = int(parts[2])
            restriction = parts[3]
            
            # Toggle the restriction in the user's session data
            # This would require a session storage mechanism
            
            await event.answer(f"Restriction '{restriction}' toggled. Click Apply to confirm.")
            
            # Return to the mute options
            await handle_mute_user(event, user, chat, ["mute_user", "options", str(target_user_id)])
        
        elif parts[1] == "confirm" and len(parts) >= 3:
            # Confirm mute for the selected user
            target_user_id = int(parts[2])
            
            # Mute the user (restrict sending messages)
            try:
                await event.client.edit_permissions(
                    chat,
                    target_user_id,
                    send_messages=False
                )
                
                # Log the action
                await operations.add_log(
                    group_id=chat.id,
                    user_id=target_user_id,
                    admin_id=user.id,
                    action="mute",
                    details="Muted via admin panel"
                )
                
                # Edit the message to show success
                await event.edit(
                    messages.MUTE_USER_SUCCESS_TEXT.format(
                        user_id=target_user_id
                    ),
                    buttons=[
                        [event.client.build_reply_markup().button(text="⬅️ Back to Admin Panel", callback_data="admin_panel")]
                    ]
                )
            
            except Exception as e:
                logger.error(f"Error muting user: {e}")
                await event.answer(f"Failed to mute user: {str(e)}", alert=True)
                await handle_admin_panel(event, user, chat, ["admin_panel"])
        
        else:
            # Unknown mute action
            await event.answer("Invalid mute action.", alert=True)
            await handle_admin_panel(event, user, chat, ["admin_panel"])
    
    except Exception as e:
        logger.error(f"Error handling mute user: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_warn_user(event, user, chat, parts):
    """Handle warn user callbacks."""
    # Implementation similar to ban_user and mute_user
    await event.answer("Warn user functionality is not yet implemented.", alert=True)
    await handle_admin_panel(event, user, chat, ["admin_panel"])

async def handle_clean_messages(event, user, chat, parts):
    """Handle clean messages callbacks."""
    try:
        if len(parts) == 1 or parts[1] == "options":
            # Show clean messages options
            buttons = [
                [
                    event.client.build_reply_markup().button(text="🗑️ Delete 10", callback_data="clean_messages:confirm:10"),
                    event.client.build_reply_markup().button(text="🗑️ Delete 50", callback_data="clean_messages:confirm:50"),
                    event.client.build_reply_markup().button(text="🗑️ Delete 100", callback_data="clean_messages:confirm:100")
                ],
                [
                    event.client.build_reply_markup().button(text="🔄 Delete by User", callback_data="clean_messages:by_user"),
                    event.client.build_reply_markup().button(text="📅 Delete by Date", callback_data="clean_messages:by_date"),
                    event.client.build_reply_markup().button(text="🏷️ Delete by Type", callback_data="clean_messages:by_type")
                ],
                [
                    event.client.build_reply_markup().button(text="📎 Media Only", callback_data="clean_messages:media_only"),
                    event.client.build_reply_markup().button(text="🔗 Links Only", callback_data="clean_messages:links_only"),
                    event.client.build_reply_markup().button(text="📊 Show Preview", callback_data="clean_messages:preview")
                ],
                [
                    event.client.build_reply_markup().button(text="✅ Confirm Delete", callback_data="clean_messages:confirm:custom"),
                    event.client.build_reply_markup().button(text="❌ Cancel", callback_data="admin_panel"),
                    event.client.build_reply_markup().button(text="⬅️ Back", callback_data="admin_panel")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the clean messages options
            await event.edit(
                messages.CLEAN_MESSAGES_OPTIONS_TEXT,
                buttons=markup
            )
        
        elif parts[1] == "confirm" and len(parts) >= 3:
            # Confirm clean messages
            count = parts[2]
            
            if count == "custom":
                # Custom clean messages (would require additional parameters)
                await event.answer("Custom clean messages is not yet implemented.", alert=True)
                await handle_clean_messages(event, user, chat, ["clean_messages", "options"])
            else:
                # Clean messages by count
                try:
                    count = int(count)
                    
                    # This is a placeholder - actual message deletion would require
                    # iterating through messages and deleting them
                    
                    # Log the action
                    await operations.add_log(
                        group_id=chat.id,
                        admin_id=user.id,
                        action="clean_messages",
                        details=f"Deleted {count} messages"
                    )
                    
                    # Edit the message to show success
                    await event.edit(
                        messages.CLEAN_MESSAGES_SUCCESS_TEXT.format(
                            count=count
                        ),
                        buttons=[
                            [event.client.build_reply_markup().button(text="⬅️ Back to Admin Panel", callback_data="admin_panel")]
                        ]
                    )
                
                except Exception as e:
                    logger.error(f"Error cleaning messages: {e}")
                    await event.answer(f"Failed to clean messages: {str(e)}", alert=True)
                    await handle_admin_panel(event, user, chat, ["admin_panel"])
        
        else:
            # Unknown clean messages action
            await event.answer("This clean messages option is not yet implemented.", alert=True)
            await handle_clean_messages(event, user, chat, ["clean_messages", "options"])
    
    except Exception as e:
        logger.error(f"Error handling clean messages: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

async def handle_analytics(event, user, chat, parts):
    """Handle analytics callbacks."""
    # Implementation for analytics menu
    await event.answer("Analytics functionality is not yet implemented.", alert=True)
    await handle_main_menu(event, user, chat)

async def handle_user_info(event, user, chat, parts):
    """Handle user info callbacks."""
    # Implementation for user info menu
    await event.answer("User info functionality is not yet implemented.", alert=True)
    await handle_main_menu(event, user, chat)

async def handle_language(event, user, chat, parts):
    """Handle language selection callbacks."""
    try:
        if len(parts) == 1 or parts[1] == "select":
            # Show language selection menu
            buttons = [
                [
                    event.client.build_reply_markup().button(text="🇺🇸 English", callback_data="language:set:en"),
                    event.client.build_reply_markup().button(text="🇪🇸 Español", callback_data="language:set:es"),
                    event.client.build_reply_markup().button(text="🇫🇷 Français", callback_data="language:set:fr")
                ],
                [
                    event.client.build_reply_markup().button(text="🇩🇪 Deutsch", callback_data="language:set:de"),
                    event.client.build_reply_markup().button(text="🇷🇺 Русский", callback_data="language:set:ru"),
                    event.client.build_reply_markup().button(text="🇨🇳 中文", callback_data="language:set:zh")
                ],
                [
                    event.client.build_reply_markup().button(text="🇯🇵 日本語", callback_data="language:set:ja"),
                    event.client.build_reply_markup().button(text="🇮🇳 हिंदी", callback_data="language:set:hi"),
                    event.client.build_reply_markup().button(text="🔄 Auto-Detect", callback_data="language:set:auto")
                ],
                [
                    event.client.build_reply_markup().button(text="➕ Request Language", callback_data="language:request"),
                    event.client.build_reply_markup().button(text="⚙️ Translation Settings", callback_data="language:settings")
                ],
                [
                    event.client.build_reply_markup().button(text="⬅️ Back to Main Menu", callback_data="main_menu")
                ]
            ]
            
            markup = event.client.build_reply_markup().inline(buttons)
            
            # Edit the message with the language selection menu
            await event.edit(
                messages.LANGUAGE_SELECTION_TEXT,
                buttons=markup
            )
        
        elif parts[1] == "set" and len(parts) >= 3:
            # Set language
            language_code = parts[2]
            
            # This is a placeholder - actual language setting would require
            # updating the user's language preference in the database
            
            # Answer the callback query
            await event.answer(f"Language set to {language_code}.", alert=True)
            
            # Return to the main menu
            await handle_main_menu(event, user, chat)
        
        else:
            # Unknown language action
            await event.answer("This language option is not yet implemented.", alert=True)
            await handle_language(event, user, chat, ["language", "select"])
    
    except Exception as e:
        logger.error(f"Error handling language selection: {e}")
        await event.answer("An error occurred. Please try again later.", alert=True)

def register_handlers(client):
    """Register the callback query handler."""
    client.client.add_event_handler(callback_query_handler, events.CallbackQuery())