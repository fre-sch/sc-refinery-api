"""
Database schema
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Unicode, \
    DateTime, func, UniqueConstraint, Float, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)
    mail = Column(Unicode(250), nullable=False, unique=True)
    password_hash = Column(Unicode(64), nullable=False)
    is_google = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime)

    scopes = relationship("UserScope", back_populates="user",
                          cascade="all, delete-orphan")
    sessions_invited = relationship("MiningSessionUser", back_populates="user")
    entries = relationship("MiningSessionEntry", back_populates="user")
    sessions_created = relationship("MiningSession", back_populates="creator")
    login_sessions = relationship("UserSession", back_populates="user")

    friends_outgoing = relationship("Friendship", back_populates="user",
                                    primaryjoin="User.id==Friendship.user_id",
                                    foreign_keys="Friendship.user_id",
                                    cascade="all, delete-orphan")
    friends_incoming = relationship("Friendship", back_populates="user",
                                    primaryjoin="User.id==Friendship.friend_id",
                                    foreign_keys="Friendship.friend_id")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class UserScope(Base):
    __tablename__ = "user_scope"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    scope = Column(Unicode(50), nullable=False, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="scopes")

    __table_args__ = (
        UniqueConstraint("user_id", "scope", name="user_scope"),
        {
            "sqlite_autoincrement": True
        },
    )


class UserSession(Base):
    __tablename__ = "user_session"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    user_ip = Column(Unicode(15), nullable=False, primary_key=True)
    salt = Column(Integer, nullable=False, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="login_sessions")


class Friendship(Base):
    __tablename__ = "friendship"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    friend_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"),
                       nullable=False, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())
    confirmed = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id],
                        back_populates="friends_outgoing")
    friend = relationship("User", foreign_keys=[friend_id],
                          back_populates="friends_incoming")


class Station(Base):
    __tablename__ = "station"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(Unicode(50), nullable=False, unique=True)
    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())

    efficiencies = relationship("StationOre", back_populates="station",
                                cascade="all, delete-orphan")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class Ore(Base):
    __tablename__ = "ore"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(Unicode(50), nullable=False, unique=True)
    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())

    efficiencies = relationship("MethodOre", back_populates="ore")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class StationOre(Base):
    __tablename__ = "station_ore"

    station_id = Column(Integer, ForeignKey("station.id", ondelete="CASCADE"),
                        nullable=False, primary_key=True)
    ore_id = Column(Integer, ForeignKey("ore.id", ondelete="CASCADE"),
                    nullable=False, primary_key=True)
    efficiency_bonus = Column(Float, nullable=False, default=0.0)
    ore = relationship("Ore")
    station = relationship("Station", back_populates="efficiencies")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class Method(Base):
    __tablename__ = "method"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(Unicode(50), nullable=False, unique=True)
    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())

    efficiencies = relationship("MethodOre", back_populates="method",
                                cascade="all, delete-orphan")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class MethodOre(Base):
    __tablename__ = "method_ore"

    method_id = Column(Integer, ForeignKey("method.id", ondelete="CASCADE"),
                       nullable=False, primary_key=True)
    ore_id = Column(Integer, ForeignKey("ore.id", ondelete="CASCADE"),
                    nullable=False, primary_key=True)
    efficiency = Column(Float, nullable=False, default=0.0)
    duration = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=False, default=0.0)

    ore = relationship("Ore")
    method = relationship("Method", back_populates="efficiencies")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class MiningSession(Base):
    __tablename__ = "mining_session"

    id = Column(Integer, nullable=False, primary_key=True)
    creator_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"),
                        nullable=True)
    name = Column(Unicode(50), nullable=False)
    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())
    archived = Column(DateTime, nullable=True)
    yield_scu = Column(Float, nullable=False, default=0.0)
    yield_uec = Column(Float, nullable=False, default=0.0)

    creator = relationship("User", back_populates="sessions_created")
    users_invited = relationship("MiningSessionUser", back_populates="session")
    entries = relationship("MiningSessionEntry", back_populates="session")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class MiningSessionUser(Base):
    __tablename__ = "mining_session_user"

    session_id = Column(Integer,
                        ForeignKey("mining_session.id", ondelete="CASCADE"),
                        nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"),
                     nullable=False, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="sessions_invited")
    session = relationship("MiningSession", back_populates="users_invited")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


class MiningSessionEntry(Base):
    __tablename__ = "mining_session_entry"

    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(Integer, ForeignKey("mining_session.id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("station.id", ondelete="SET NULL"), nullable=True)
    ore_id = Column(Integer, ForeignKey("ore.id", ondelete="SET NULL"), nullable=True)
    method_id = Column(Integer, ForeignKey("method.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Float, nullable=False, default=0.0)
    duration = Column(Float, nullable=False, default=0.0)

    created = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now())

    session = relationship("MiningSession", back_populates="entries")
    station = relationship("Station")
    ore = relationship("Ore")
    method = relationship("Method")
    user = relationship("User", back_populates="entries")

    __table_args__ = (
        {
            "sqlite_autoincrement": True
        },
    )


MiningSession.entries_count = column_property(
        select([func.count(MiningSessionEntry.id)])
        .where(MiningSessionEntry.session_id == MiningSession.id)
        .correlate_except(MiningSessionEntry)
        .scalar_subquery()
    )

MiningSession.users_invited_count = column_property(
        select([func.count(MiningSessionUser.user_id)])
        .where(MiningSessionUser.session_id == MiningSession.id)
        .correlate_except(MiningSessionUser)
        .scalar_subquery()
    )