import logging

from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from screfinery.stores import user_store
from screfinery.util import parse_cookie_header, is_user_authorized

log = logging.getLogger(__name__)


def use_db(request: Request):
    app = request.app
    db_session_maker = app.state.db_session
    db_session = db_session_maker()
    try:
        yield db_session
    finally:
        db_session.close()


def use_config(request: Request):
    app = request.app
    config = app.state.config
    try:
        yield config
    finally:
        pass


def verify_user_session(request: Request, db: Session = Depends(use_db)):
    user_session = _request_verify_user_session(request, db)
    if user_session is None:
        raise HTTPException(HTTP_401_UNAUTHORIZED)
    request.state.user_session = user_session
    try:
        yield user_session
    finally:
        pass


def _cookie_session_vars(request: Request):
    cookies = parse_cookie_header(request.headers.get("cookie"))
    user_session_hash = cookies.get("s")
    user_id = cookies.get("u")
    return user_id, user_session_hash


def _request_verify_user_session(request: Request, db: Session):
    user_ip = request.client.host
    user_id, cookie_session_hash = _cookie_session_vars(request)
    if cookie_session_hash is None or user_id is None:
        log.warning(f"missing session vars: user_id:{user_id}"
                    f", user_ip:{user_ip}"
                    f", user_session_hash:{cookie_session_hash}")
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    db_session, db_session_hash = user_store.find_session(db, user_id)
    if db_session is None:
        log.warning(f"session not found for user_id: {user_id}")
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    request_session_hash = user_store.session_hash(user_id, user_ip, db_session.salt)
    is_valid_session = (
        db_session_hash == request_session_hash == cookie_session_hash
    )
    if not is_valid_session:
        log.warning(f"session hash invalid for user_id: {user_id}")
        raise HTTPException(HTTP_403_FORBIDDEN)
    return db_session
