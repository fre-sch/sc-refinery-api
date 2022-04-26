"""
CRUD methods for `user` objects.
"""
import logging
from datetime import datetime
from hashlib import sha256
from random import randint
from time import time
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session, joinedload

from screfinery import schema
from screfinery.stores.model import User, UserScope, UserSession
from screfinery.util import hash_password, sa_filter_from_dict, \
    sa_order_by_from_dict

log = logging.getLogger(__name__)
resource_name = "user"


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return (
        db.query(User)
        .options(joinedload(User.scopes))
        .options(joinedload(User.friends))
        .options(joinedload(User.sessions_invited))
        .filter(User.id == user_id)
        .first()
    )


def get_by_ids(db: Session, user_ids: List[int]) -> List[User]:
    return db.query(User).filter(User.id.in_(user_ids)).all()


def list_all(db: Session,
             offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None) -> Tuple[int, List[User]]:
    filter_ = sa_filter_from_dict(User, filter_)
    order_by = sa_order_by_from_dict(User, sort)
    return (
        db.query(User).filter(filter_).count(),
        (
            db.query(User)
            .filter(filter_)
            .order_by(*order_by)
            .options(joinedload(User.scopes))
            .offset(offset)
            .limit(limit)
            .all()
        )
    )


def create_one(db: Session, user: schema.UserCreate, password_salt: str) -> User:
    db_user = User(
        name=user.name,
        mail=user.mail.strip().lower(),
        password_hash=hash_password(password_salt, user.password_confirm),
        is_google=user.is_google,
        is_active=user.is_active,
    )
    db_user.scopes = [
        UserScope(user=db_user, scope=scope)
        for scope in user.scopes
    ]
    db.add(db_user)
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
    if user.scopes is not None:
        db_user.scopes = [
            UserScope(user=db_user, scope=scope)
            for scope in user.scopes
        ]
    if user.friends is not None:
        db_user.friends = db.query(User).filter(
            User.id.in_(it.id for it in user.friends)
        ).all()
    log.info(f"Updating user {user}")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def find_by_credentials(db: Session, mail: str, password_hash: str) -> Optional[User]:
    return (
        db.query(User)
        .options(joinedload(User.scopes))
        .filter(User.mail == mail.strip().lower(),
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


def create_session(db: Session, user: User, user_ip: str) -> Tuple[UserSession, str]:
    user.last_login = datetime.utcnow()
    session_salt = int(time()) ^ randint(0, 2**24)
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    user_session = UserSession(user=user, user_ip=user_ip, salt=session_salt)
    db.add(user_session)
    db.commit()
    db.refresh(user_session)
    return user_session, session_hash(user.id, user_ip, session_salt)


def find_session(db: Session, user_id: int) -> Optional[Tuple[UserSession, str]]:
    session = (
        db.query(UserSession)
        .options(
            joinedload(UserSession.user)
            .joinedload(User.scopes)
        )
        .filter(UserSession.user_id == user_id)
        .first()
    )
    if session is None:
        return
    return session, session_hash(session.user_id, session.user_ip, session.salt)


def delete_session(db: Session, session) -> None:
    db.query(UserSession).filter(UserSession.user_id == session.user_id).delete()
    db.commit()
