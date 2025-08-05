"""
Message templates for the bot.
Variables in curly braces will be replaced with actual values.
"""

# Bot Messages
START_MESSAGE = """
👋 Hello {mention}!

I'm {bot_name}, a powerful group protection bot designed to keep your Telegram groups safe from spam, raids, and unwanted content.

Use /help to see available commands.
"""

HELP_MESSAGE = """
📚 **Available Commands**

**User Commands:**
/start - Start the bot
/help - Show this help message
/info - Show user/chat information
/rules - Display group rules
/report [@user] [reason] - Report user to admins

**Admin Commands:**
/ban [@user] [reason] [time] - Ban user
/unban [@user] - Unban user
/kick [@user] [reason] - Kick user
/mute [@user] [time] [reason] - Mute user
/unmute [@user] - Unmute user
/warn [@user] [reason] - Warn user
/unwarn [@user] - Remove warning
/pin [reply] - Pin message
/unpin - Unpin message

**Group Settings:**
/settings - Show group settings panel
/welcome [message] - Set welcome message
/goodbye [message] - Set goodbye message
/rules [text] - Set group rules
/antispam [on/off] - Toggle anti-spam system

For more information, contact {owner_username} or visit our support group.
"""

INFO_MESSAGE = """
ℹ️ **Information**

**User:** {user_mention} ({user_id})
**Username:** @{username}
**First Name:** {first_name}
**Last Name:** {last_name}
**User Link:** [Link to Profile](tg://user?id={user_id})
**Status:** {user_status}

**Chat:** {chat_title} ({chat_id})
**Chat Type:** {chat_type}
**Member Count:** {member_count}
**Created On:** {created_date}
"""

# Admin Messages
BAN_MESSAGE = "🚫 {admin} banned {user_mention} {reason_text}. {time_text}"
UNBAN_MESSAGE = "✅ {admin} unbanned {user_mention}."
KICK_MESSAGE = "👢 {admin} kicked {user_mention} {reason_text}."
MUTE_MESSAGE = "🔇 {admin} muted {user_mention} {time_text} {reason_text}."
UNMUTE_MESSAGE = "🔊 {admin} unmuted {user_mention}."
WARN_MESSAGE = "⚠️ {admin} warned {user_mention} {reason_text}. Warnings: {warn_count}/{warn_limit}"
UNWARN_MESSAGE = "✅ {admin} removed a warning from {user_mention}. Warnings: {warn_count}/{warn_limit}"
PIN_MESSAGE = "📌 {admin} pinned a message."
UNPIN_MESSAGE = "📍 {admin} unpinned a message."

# Error Messages
NOT_ADMIN_ERROR = "❌ You must be an admin to use this command."
BOT_NOT_ADMIN_ERROR = "❌ I need to be an admin with appropriate permissions to perform this action."
USER_NOT_FOUND_ERROR = "❌ User not found."
USER_IS_ADMIN_ERROR = "❌ I can't perform this action on an admin."
INVALID_TIME_FORMAT_ERROR = "❌ Invalid time format. Use a number followed by 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days)."
INVALID_COMMAND_FORMAT_ERROR = "❌ Invalid command format. Use {command_format}"
GENERAL_ERROR = "❌ An error occurred: {error_message}"

# Welcome and Goodbye
DEFAULT_WELCOME = "👋 Welcome {mention} to {chat_title}! Please read the rules."
DEFAULT_GOODBYE = "👋 {mention} left {chat_title}."
RULES_MESSAGE = """
📜 **Group Rules**

{rules_text}

Please follow these rules to maintain a friendly environment.
"""

# Anti-Spam Messages
SPAM_DETECTED = "🚨 Spam detected from {user_mention}. Action taken: {action}"
RAID_DETECTED = "🚨 Possible raid detected! {count} new users joined in the last {time} seconds."
LINK_FILTERED = "🔗 Link from {user_mention} was removed due to our link policy."
MEDIA_FILTERED = "🖼️ Media from {user_mention} was removed due to our media policy."

# Settings Messages
SETTINGS_MESSAGE = """
⚙️ **Group Settings**

**Anti-Spam:** {antispam_status}
**Link Filtering:** {link_filtering_status}
**Media Filtering:** {media_filtering_status}
**Welcome Messages:** {welcome_messages_status}
**Goodbye Messages:** {goodbye_messages_status}
**Auto-Delete Commands:** {auto_delete_commands_status}

Use the buttons below to change settings.
"""

# Callback Responses
SETTING_UPDATED = "✅ Setting updated successfully!"
SETTING_UNCHANGED = "ℹ️ Setting remains unchanged."