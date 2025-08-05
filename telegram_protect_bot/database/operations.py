from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging

from telegram_protect_bot.config import settings
from telegram_protect_bot.database.models import Base, Group, User, GroupUser, Warning, Ban, Filter, Log

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Initialize logger
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)
    logger.info("Database initialized")

def get_or_create_group(group_id, title=None, username=None):
    """Get a group by ID or create it if it doesn't exist."""
    session = Session()
    try:
        group = session.query(Group).filter(Group.id == group_id).first()
        if not group:
            group = Group(id=group_id, title=title, username=username)
            session.add(group)
            session.commit()
            logger.info(f"Created new group: {title} ({group_id})")
        elif title and group.title != title:
            group.title = title
            session.commit()
            logger.info(f"Updated group title: {title} ({group_id})")
        return group
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in get_or_create_group: {e}")
        return None
    finally:
        session.close()

def get_or_create_user(user_id, first_name, last_name=None, username=None, is_bot=False):
    """Get a user by ID or create it if it doesn't exist."""
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                is_bot=is_bot
            )
            session.add(user)
            session.commit()
            logger.info(f"Created new user: {first_name} ({user_id})")
        else:
            # Update user information if changed
            updated = False
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if user.username != username:
                user.username = username
                updated = True
            
            if updated:
                session.commit()
                logger.info(f"Updated user information: {first_name} ({user_id})")
                
        return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in get_or_create_user: {e}")
        return None
    finally:
        session.close()

def add_user_to_group(user_id, group_id, is_admin=False, admin_title=None):
    """Add a user to a group or update their status."""
    session = Session()
    try:
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id
        ).first()
        
        if not group_user:
            group_user = GroupUser(
                user_id=user_id,
                group_id=group_id,
                is_admin=is_admin,
                admin_title=admin_title,
                join_date=datetime.utcnow()
            )
            session.add(group_user)
            session.commit()
            logger.info(f"Added user {user_id} to group {group_id}")
        else:
            # Update admin status if changed
            if group_user.is_admin != is_admin or group_user.admin_title != admin_title:
                group_user.is_admin = is_admin
                group_user.admin_title = admin_title
                session.commit()
                logger.info(f"Updated user {user_id} admin status in group {group_id}")
                
        return group_user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in add_user_to_group: {e}")
        return None
    finally:
        session.close()

def remove_user_from_group(user_id, group_id):
    """Remove a user from a group."""
    session = Session()
    try:
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id
        ).first()
        
        if group_user:
            session.delete(group_user)
            session.commit()
            logger.info(f"Removed user {user_id} from group {group_id}")
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in remove_user_from_group: {e}")
        return False
    finally:
        session.close()

def update_user_activity(user_id, group_id):
    """Update a user's last activity time and message count in a group."""
    session = Session()
    try:
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id
        ).first()
        
        if group_user:
            group_user.last_active = datetime.utcnow()
            group_user.message_count += 1
            session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in update_user_activity: {e}")
        return False
    finally:
        session.close()

def add_warning(user_id, group_id, admin_id, reason=None):
    """Add a warning to a user in a group."""
    session = Session()
    try:
        warning = Warning(
            user_id=user_id,
            group_id=group_id,
            admin_id=admin_id,
            reason=reason,
            date=datetime.utcnow()
        )
        session.add(warning)
        
        # Update warning count in GroupUser
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id
        ).first()
        
        if group_user:
            group_user.warning_count += 1
            
        session.commit()
        logger.info(f"Added warning to user {user_id} in group {group_id}")
        
        # Return the updated warning count
        return group_user.warning_count if group_user else 1
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in add_warning: {e}")
        return 0
    finally:
        session.close()

def remove_warning(user_id, group_id):
    """Remove the most recent warning from a user in a group."""
    session = Session()
    try:
        # Get the most recent warning
        warning = session.query(Warning).filter(
            Warning.user_id == user_id,
            Warning.group_id == group_id
        ).order_by(Warning.date.desc()).first()
        
        if warning:
            session.delete(warning)
            
            # Update warning count in GroupUser
            group_user = session.query(GroupUser).filter(
                GroupUser.user_id == user_id,
                GroupUser.group_id == group_id
            ).first()
            
            if group_user and group_user.warning_count > 0:
                group_user.warning_count -= 1
                
            session.commit()
            logger.info(f"Removed warning from user {user_id} in group {group_id}")
            
            # Return the updated warning count
            return group_user.warning_count if group_user else 0
        return None
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in remove_warning: {e}")
        return None
    finally:
        session.close()

def get_warning_count(user_id, group_id):
    """Get the number of warnings a user has in a group."""
    session = Session()
    try:
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id
        ).first()
        
        if group_user:
            return group_user.warning_count
        return 0
    except SQLAlchemyError as e:
        logger.error(f"Error in get_warning_count: {e}")
        return 0
    finally:
        session.close()

def add_ban(user_id, group_id, admin_id, reason=None, duration=None):
    """Ban a user from a group."""
    session = Session()
    try:
        # Calculate until_date if duration is provided
        until_date = None
        if duration:
            until_date = datetime.utcnow() + timedelta(seconds=duration)
            
        # Check if there's an active ban
        existing_ban = session.query(Ban).filter(
            Ban.user_id == user_id,
            Ban.group_id == group_id,
            Ban.is_active == True
        ).first()
        
        if existing_ban:
            # Update existing ban
            existing_ban.admin_id = admin_id
            existing_ban.reason = reason
            existing_ban.date = datetime.utcnow()
            existing_ban.until_date = until_date
            ban = existing_ban
        else:
            # Create new ban
            ban = Ban(
                user_id=user_id,
                group_id=group_id,
                admin_id=admin_id,
                reason=reason,
                date=datetime.utcnow(),
                until_date=until_date,
                is_active=True
            )
            session.add(ban)
            
        session.commit()
        logger.info(f"Banned user {user_id} from group {group_id}")
        return ban
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in add_ban: {e}")
        return None
    finally:
        session.close()

def remove_ban(user_id, group_id):
    """Unban a user from a group."""
    session = Session()
    try:
        # Find active bans
        bans = session.query(Ban).filter(
            Ban.user_id == user_id,
            Ban.group_id == group_id,
            Ban.is_active == True
        ).all()
        
        if bans:
            for ban in bans:
                ban.is_active = False
                
            session.commit()
            logger.info(f"Unbanned user {user_id} from group {group_id}")
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in remove_ban: {e}")
        return False
    finally:
        session.close()

def is_user_banned(user_id, group_id):
    """Check if a user is banned from a group."""
    session = Session()
    try:
        # Check for active bans
        ban = session.query(Ban).filter(
            Ban.user_id == user_id,
            Ban.group_id == group_id,
            Ban.is_active == True
        ).first()
        
        if ban:
            # If ban has expired, remove it
            if ban.until_date and ban.until_date < datetime.utcnow():
                ban.is_active = False
                session.commit()
                return False
            return True
        return False
    except SQLAlchemyError as e:
        logger.error(f"Error in is_user_banned: {e}")
        return False
    finally:
        session.close()

def add_filter(group_id, keyword, created_by, is_regex=False, is_blacklist=True):
    """Add a filter to a group."""
    session = Session()
    try:
        # Check if filter already exists
        existing_filter = session.query(Filter).filter(
            Filter.group_id == group_id,
            Filter.keyword == keyword
        ).first()
        
        if not existing_filter:
            filter_obj = Filter(
                group_id=group_id,
                keyword=keyword,
                is_regex=is_regex,
                is_blacklist=is_blacklist,
                created_by=created_by,
                created_at=datetime.utcnow()
            )
            session.add(filter_obj)
            session.commit()
            logger.info(f"Added filter '{keyword}' to group {group_id}")
            return filter_obj
        return existing_filter
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in add_filter: {e}")
        return None
    finally:
        session.close()

def remove_filter(group_id, keyword):
    """Remove a filter from a group."""
    session = Session()
    try:
        filter_obj = session.query(Filter).filter(
            Filter.group_id == group_id,
            Filter.keyword == keyword
        ).first()
        
        if filter_obj:
            session.delete(filter_obj)
            session.commit()
            logger.info(f"Removed filter '{keyword}' from group {group_id}")
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in remove_filter: {e}")
        return False
    finally:
        session.close()

def get_filters(group_id):
    """Get all filters for a group."""
    session = Session()
    try:
        filters = session.query(Filter).filter(
            Filter.group_id == group_id
        ).all()
        return filters
    except SQLAlchemyError as e:
        logger.error(f"Error in get_filters: {e}")
        return []
    finally:
        session.close()

def add_log(action, group_id=None, user_id=None, admin_id=None, details=None):
    """Add a log entry."""
    session = Session()
    try:
        log = Log(
            group_id=group_id,
            user_id=user_id,
            admin_id=admin_id,
            action=action,
            details=details,
            date=datetime.utcnow()
        )
        session.add(log)
        session.commit()
        return log
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in add_log: {e}")
        return None
    finally:
        session.close()

def get_group_settings(group_id):
    """Get all settings for a group."""
    session = Session()
    try:
        group = session.query(Group).filter(Group.id == group_id).first()
        return group
    except SQLAlchemyError as e:
        logger.error(f"Error in get_group_settings: {e}")
        return None
    finally:
        session.close()

def update_group_settings(group_id, **kwargs):
    """Update group settings."""
    session = Session()
    try:
        group = session.query(Group).filter(Group.id == group_id).first()
        if group:
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            session.commit()
            logger.info(f"Updated settings for group {group_id}")
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in update_group_settings: {e}")
        return False
    finally:
        session.close()

def check_raid(group_id, threshold=10, window=60):
    """Check if a raid is happening (many users joining in a short time)."""
    session = Session()
    try:
        # Count users who joined in the last 'window' seconds
        time_threshold = datetime.utcnow() - timedelta(seconds=window)
        join_count = session.query(func.count(GroupUser.user_id)).filter(
            GroupUser.group_id == group_id,
            GroupUser.join_date >= time_threshold
        ).scalar()
        
        return join_count >= threshold
    except SQLAlchemyError as e:
        logger.error(f"Error in check_raid: {e}")
        return False
    finally:
        session.close()

def check_spam_score(user_id, group_id):
    """Calculate a user's spam score based on various factors."""
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
            
        score = 0
        
        # Factor 1: Warning count
        warning_count = get_warning_count(user_id, group_id)
        score += warning_count * 20  # Each warning adds 20 points
        
        # Factor 2: Account age
        account_age = (datetime.utcnow() - user.join_date).days
        if account_age < 1:
            score += 30  # New account (less than 1 day)
        elif account_age < 7:
            score += 15  # Account less than a week old
            
        # Factor 3: Message frequency
        time_window = datetime.utcnow() - timedelta(minutes=5)
        message_count = session.query(func.count(Log.id)).filter(
            Log.user_id == user_id,
            Log.group_id == group_id,
            Log.action == 'message',
            Log.date >= time_window
        ).scalar()
        
        if message_count > 20:
            score += 40  # More than 20 messages in 5 minutes
        elif message_count > 10:
            score += 20  # More than 10 messages in 5 minutes
            
        # Factor 4: Reputation score
        if user.reputation_score < 50:
            score += 30
        elif user.reputation_score < 75:
            score += 15
            
        # Factor 5: Blacklist/Whitelist
        if user.is_blacklisted:
            score += 100
        if user.is_whitelisted:
            score = 0  # Whitelisted users get a score of 0
            
        return min(score, 100)  # Cap at 100
    except SQLAlchemyError as e:
        logger.error(f"Error in check_spam_score: {e}")
        return 0
    finally:
        session.close()

def is_admin(user_id, group_id):
    """Check if a user is an admin in a group."""
    session = Session()
    try:
        group_user = session.query(GroupUser).filter(
            GroupUser.user_id == user_id,
            GroupUser.group_id == group_id,
            GroupUser.is_admin == True
        ).first()
        
        return bool(group_user)
    except SQLAlchemyError as e:
        logger.error(f"Error in is_admin: {e}")
        return False
    finally:
        session.close()

def get_group_admins(group_id):
    """Get all admins in a group."""
    session = Session()
    try:
        admins = session.query(User).join(GroupUser).filter(
            GroupUser.group_id == group_id,
            GroupUser.is_admin == True
        ).all()
        
        return admins
    except SQLAlchemyError as e:
        logger.error(f"Error in get_group_admins: {e}")
        return []
    finally:
        session.close()