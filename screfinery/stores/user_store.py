"""
CRUD methods for `user` objects.
"""
import logging
from random import randint
from time import time
from typing import Optional

from sqlalchemy.orm import Session, joinedload, contains_eager

from screfinery import schema
from screfinery.stores.model import User, UserScope, UserSession
from hashlib import sha256


log = logging.getLogger(__name__)
resource_name = "user"


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return (
        db.query(User)
        .options(joinedload(User.scopes))
        .filter(User.id == user_id)
        .first()
    )


def list_all(db: Session, offset: int, limit: int) -> tuple[int, list[User]]:
    return (
        db.query(User).count(),
        (
            db.query(User)
            .options(joinedload(User.scopes))
            .offset(offset)
            .limit(limit)
            .all()
        )
    )


def _update_user_scopes(db: Session, user: User, scopes: list[str]):
    if scopes is None:
        return
    db.query(UserScope).filter(UserScope.user == user).delete()
    for scope in scopes:
        db_scope = UserScope(user=user, scope=scope)
        db.add(db_scope)


def create_one(db: Session, user: schema.UserCreate) -> User:
    db_user = User(
        name=user.name,
        mail=user.mail,
        password_hash=sha256(user.password.encode("utf-8")).hexdigest(),
        is_google=user.is_google,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    _update_user_scopes(db, db_user, user.scopes)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_by_id(db: Session, user_id: int):
    db.query(User).filter(User.id == user_id).delete()
    db.commit()


def update_by_id(db: Session, user_id: int, user: schema.UserUpdate) -> Optional[User]:
    db_user = get_by_id(db, user_id)
    if db_user is None:
        return None
    if user.name:
        db_user.name = user.name
    if user.mail:
        db_user.mail = user.mail
    if user.is_active:
        db_user.is_active = user.is_active
    if user.is_google:
        db_user.is_google = user.is_google
    if user.password:
        db_user.password_hash = user.password
    log.info(f"Updating user {user}")
    _update_user_scopes(db, db_user, user.scopes)
    db.add(db_user)
    db.commit()
    return db_user


def find_by_credentials(db: Session, mail: str, password_hash: str) -> Optional[User]:
    return (
        db.query(User)
        .options(joinedload(User.scopes))
        .filter(User.mail == mail,
                User.password_hash == password_hash,
                User.is_active == True)
        .first()
    )


def delete_sessions(db: Session, user_id: int) -> None:
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()


def session_hash(user_id, user_ip, salt) -> str:
    hash_value = f"{user_id}/{user_ip}/{salt}"
    return sha256(hash_value.encode("utf-8")).hexdigest()


def create_session(db: Session, user: User, user_ip: str) -> tuple[UserSession, str]:
    session_salt = int(time()) ^ randint(0, 2**32)
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    user_session = UserSession(user=user, user_ip=user_ip, salt=session_salt)
    db.add(user_session)
    db.commit()
    return user_session, session_hash(user.id, user_ip, session_salt)


def find_session(db: Session, user_id: int) -> Optional[tuple[UserSession, str]]:
    session = (
        db.query(UserSession)
        .options(joinedload(UserSession.user)
        .options(joinedload(User.scopes)))
        .filter(UserSession.user_id == user_id)
        .first()
    )
    if session is None:
        return
    return session, session_hash(session.user_id, session.user_ip, session.salt)

