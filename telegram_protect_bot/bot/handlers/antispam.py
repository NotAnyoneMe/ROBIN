from telethon import events
import asyncio
import re

from telegram_protect_bot.config import settings
from telegram_protect_bot.database import operations as db
from telegram_protect_bot.bot.utils import helpers, permissions, decorators

async def setup(client):
    """Set up anti-spam handlers."""
    
    @client.add_event_handler
    @decorators.handle_errors
    async def on_message(event):
        """Handle new messages for spam detection."""
        # Skip messages in private chats
        if event.is_private:
            return
            
        # Skip messages from admins
        chat_id = event.chat_id
        user_id = event.sender_id
        
        if await permissions.is_user_admin(client.client, chat_id, user_id):
            return
            
        # Get chat and user information
        chat = await event.get_chat()
        user = await event.get_user()
        
        # Update database
        db.get_or_create_group(chat_id, chat.title, getattr(chat, 'username', None))
        db.get_or_create_user(
            user.id,
            user.first_name,
            user.last_name,
            user.username,
            getattr(user, 'bot', False)
        )
        db.update_user_activity(user_id, chat_id)
        
        # Get group settings
        group_settings = db.get_group_settings(chat_id)
        if not group_settings or not group_settings.antispam_enabled:
            return
            
        # Check if user is banned
        if db.is_user_banned(user_id, chat_id):
            try:
                await event.delete()
            except Exception as e:
                print(f"Error deleting message from banned user: {e}")
            return
            
        # Get message text
        message_text = event.text or event.message.message
        if not message_text:
            return
            
        # Check for spam indicators
        spam_detected = False
        spam_reason = None
        
        # 1. Check message rate limiting
        if helpers.rate_limit_check(
            user_id,
            'message',
            group_settings.message_limit,
            group_settings.message_window
        ):
            spam_detected = True
            spam_reason = f"Message rate limit exceeded ({group_settings.message_limit} in {group_settings.message_window}s)"
            
        # 2. Check for forwarded messages
        if event.fwd_from and helpers.rate_limit_check(
            user_id,
            'forward',
            group_settings.forward_limit,
            group_settings.forward_window
        ):
            spam_detected = True
            spam_reason = f"Forward rate limit exceeded ({group_settings.forward_limit} in {group_settings.forward_window}s)"
            
        # 3. Check for links if enabled
        if group_settings.link_filtering_enabled and helpers.is_valid_url(message_text):
            # Check link rate limiting
            if helpers.rate_limit_check(user_id, 'link', group_settings.link_limit, 60):
                spam_detected = True
                spam_reason = f"Link rate limit exceeded ({group_settings.link_limit} in 60s)"
                
        # 4. Check for mentions
        mention_count = helpers.count_mentions(message_text)
        if mention_count > group_settings.mention_limit:
            spam_detected = True
            spam_reason = f"Too many mentions ({mention_count})"
            
        # 5. Check for blacklisted words
        filters = db.get_filters(chat_id)
        blacklisted_words = [f.keyword for f in filters if f.is_blacklist]
        if helpers.contains_blacklisted_words(message_text, blacklisted_words):
            spam_detected = True
            spam_reason = "Blacklisted word detected"
            
        # 6. Check language if enabled
        if group_settings.language_detection_enabled:
            detected_lang = helpers.detect_language(message_text)
            # This is a placeholder - you would need to implement language filtering
            # based on allowed languages for each group
            
        # Calculate spam score
        spam_score = db.check_spam_score(user_id, chat_id)
        
        # Take action if spam detected or score too high
        if spam_detected or spam_score >= settings.SPAM_SCORE_THRESHOLD:
            # Delete the message
            try:
                await event.delete()
            except Exception as e:
                print(f"Error deleting spam message: {e}")
                
            # Log the spam
            db.add_log(
                action="spam_detected",
                group_id=chat_id,
                user_id=user_id,
                details=spam_reason or f"Spam score: {spam_score}"
            )
            
            # Determine action based on spam score
            action = "deleted message"
            
            # Auto-warn if score is high
            if spam_score >= settings.SPAM_SCORE_THRESHOLD:
                warning_count = db.add_warning(user_id, chat_id, (await client.client.get_me()).id, spam_reason)
                action = f"warned (#{warning_count})"
                
                # Auto-ban if warning threshold reached
                if warning_count >= group_settings.warning_threshold:
                    try:
                        await client.client.edit_permissions(
                            chat_id,
                            user_id,
                            view_messages=False
                        )
                        db.add_ban(
                            user_id,
                            chat_id,
                            (await client.client.get_me()).id,
                            f"Exceeded warning threshold ({warning_count}/{group_settings.warning_threshold})"
                        )
                        action = "banned"
                    except Exception as e:
                        print(f"Error banning user: {e}")
                        
            # Auto-ban if score is very high
            elif spam_score >= settings.AUTO_BAN_SCORE:
                try:
                    await client.client.edit_permissions(
                        chat_id,
                        user_id,
                        view_messages=False
                    )
                    db.add_ban(
                        user_id,
                        chat_id,
                        (await client.client.get_me()).id,
                        f"High spam score: {spam_score}"
                    )
                    action = "banned"
                except Exception as e:
                    print(f"Error banning user: {e}")
                    
            # Notify admins
            spam_notification = f"🚨 **Spam Detected**\n\nUser: {helpers.get_user_link(user)}\nChat: {chat.title}\nReason: {spam_reason or f'Spam score: {spam_score}'}\nAction: {action}"
            await client.send_message_to_log_channel(spam_notification)
    
    # Register the event handler
    client.add_event_handler(on_message, events.NewMessage())