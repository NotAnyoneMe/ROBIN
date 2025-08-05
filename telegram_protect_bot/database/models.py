from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    username = Column(String(255), nullable=True)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Settings
    welcome_enabled = Column(Boolean, default=True)
    goodbye_enabled = Column(Boolean, default=True)
    welcome_message = Column(Text, nullable=True)
    goodbye_message = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    
    # Anti-spam settings
    antispam_enabled = Column(Boolean, default=True)
    link_filtering_enabled = Column(Boolean, default=True)
    media_filtering_enabled = Column(Boolean, default=False)
    language_detection_enabled = Column(Boolean, default=True)
    nsfw_detection_enabled = Column(Boolean, default=True)
    scam_detection_enabled = Column(Boolean, default=True)
    
    # Rate limits
    message_limit = Column(Integer, default=10)
    message_window = Column(Integer, default=60)  # seconds
    forward_limit = Column(Integer, default=5)
    forward_window = Column(Integer, default=3600)  # seconds
    mention_limit = Column(Integer, default=5)
    link_limit = Column(Integer, default=3)
    
    # Auto-moderation
    warning_threshold = Column(Integer, default=3)
    raid_threshold = Column(Integer, default=10)
    auto_delete_commands = Column(Boolean, default=True)
    command_delete_delay = Column(Integer, default=30)  # seconds
    auto_delete_welcome_time = Column(Integer, default=300)  # seconds
    
    # Relationships
    users = relationship("User", secondary="group_users", back_populates="groups")
    
    def __repr__(self):
        return f"<Group(id={self.id}, title='{self.title}')>"


class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    is_bot = Column(Boolean, default=False)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # User reputation
    reputation_score = Column(Float, default=100.0)
    is_blacklisted = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=False)
    
    # Relationships
    groups = relationship("Group", secondary="group_users", back_populates="users")
    warnings = relationship("Warning", back_populates="user")
    bans = relationship("Ban", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class GroupUser(Base):
    __tablename__ = 'group_users'
    
    group_id = Column(BigInteger, ForeignKey('groups.id'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    admin_title = Column(String(255), nullable=True)
    
    # User status in group
    warning_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    last_active = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<GroupUser(group_id={self.group_id}, user_id={self.user_id})>"


class Warning(Base):
    __tablename__ = 'warnings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    group_id = Column(BigInteger, ForeignKey('groups.id'))
    admin_id = Column(BigInteger, ForeignKey('users.id'))
    reason = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="warnings", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<Warning(id={self.id}, user_id={self.user_id}, group_id={self.group_id})>"


class Ban(Base):
    __tablename__ = 'bans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    group_id = Column(BigInteger, ForeignKey('groups.id'))
    admin_id = Column(BigInteger, ForeignKey('users.id'))
    reason = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    until_date = Column(DateTime, nullable=True)  # Null means permanent
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="bans", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<Ban(id={self.id}, user_id={self.user_id}, group_id={self.group_id})>"


class Filter(Base):
    __tablename__ = 'filters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey('groups.id'))
    keyword = Column(String(255))
    is_regex = Column(Boolean, default=False)
    is_blacklist = Column(Boolean, default=True)
    created_by = Column(BigInteger, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Filter(id={self.id}, group_id={self.group_id}, keyword='{self.keyword}')>"


class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey('groups.id'), nullable=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    admin_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    action = Column(String(255))
    details = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Log(id={self.id}, action='{self.action}')>"