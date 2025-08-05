# ROBIN - Telegram Protection Bot

A powerful Telegram bot designed to protect groups from spam, raids, and unwanted content.

## Features

- **Anti-Spam System**
  - Message flood protection
  - Forward spam detection
  - Link filtering
  - Mention spam detection
  - Duplicate message detection
  - New user restrictions
  - Auto-ban system

- **Content Moderation**
  - Media filtering
  - Text filtering with blacklists
  - Language detection
  - Scam link protection

- **User Management**
  - Welcome/goodbye messages
  - User verification
  - Warning system
  - Temporary restrictions

- **Admin Tools**
  - Ban, kick, mute commands
  - Warning management
  - Group settings configuration
  - Audit logs

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ROBIN.git
   cd ROBIN
   ```

2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

3. Copy the example environment file and edit it:
   ```
   cp .env.example .env
   nano .env
   ```

4. Run the bot:
   ```
   python main.py
   ```

## Configuration

Edit the `.env` file to configure the bot:

- `API_ID` and `API_HASH`: Get from [my.telegram.org](https://my.telegram.org)
- `BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather)
- `OWNER_ID`: Your Telegram user ID
- Other settings for anti-spam, moderation, etc.

## Commands

### User Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/info` - Show user/chat information
- `/rules` - Display group rules
- `/report` - Report a user to admins

### Admin Commands
- `/ban` - Ban a user
- `/unban` - Unban a user
- `/kick` - Kick a user
- `/mute` - Mute a user
- `/unmute` - Unmute a user
- `/warn` - Warn a user
- `/unwarn` - Remove a warning

### Settings Commands
- `/settings` - Show group settings panel
- `/welcome` - Set welcome message
- `/goodbye` - Set goodbye message
- `/setrules` - Set group rules
- `/antispam` - Toggle anti-spam system

## License

This project is licensed under the MIT License - see the LICENSE file for details.