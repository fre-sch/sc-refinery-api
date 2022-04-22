import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth import jwt
from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.dependency import use_db, use_config, verify_user_session
from screfinery.stores import user_store
from screfinery.util import hash_password, parse_cookie_header

log = logging.getLogger(__name__)
ONE_DAY = 60 * 60 * 24
auth_routes = APIRouter()


@auth_routes.post("/login", response_model=schema.User, tags=["user"])
def login(request: Request,
          login: schema.Login,
          db: Session = Depends(use_db),
          config=Depends(use_config)) -> JSONResponse:
    """
    Given a username and password, create a user session and respond with user
    and cookies ``u`` (user's id) and ``s`` (session hash).
    """
    password_hash = hash_password(config.app.password_salt, login.password)
    user = user_store.find_by_credentials(db, login.username, password_hash)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    user_session, session_hash = user_store.create_session(db, user, request.client.host)
    response = JSONResponse(
        status_code=200,
        content=jsonable_encoder(schema.User.from_orm(user))
    )
    response.set_cookie("u", user.id, path="/", max_age=ONE_DAY,
                        samesite="none", secure=True, httponly=False)
    response.set_cookie("s", session_hash, path="/", max_age=ONE_DAY,
                        samesite="none", secure=True, httponly=False)
    return response


@auth_routes.post("/login_session", response_model=schema.User, tags=["user"])
def login_session(user_session=Depends(verify_user_session)):
    return user_session.user


@auth_routes.post("/logout", tags=["user"])
def logout(db: Session = Depends(use_db),
           user_session=Depends(verify_user_session)):
    user_store.delete_session(db, user_session)
    response = JSONResponse("/")
    response.delete_cookie("u", path="/")
    response.delete_cookie("s", path="/")
    return response


@auth_routes.post("/google_signin", tags=["user"], response_class=RedirectResponse)
def google_signin(request: Request,
                  g_csrf_token: str = Form(...),
                  credential: str = Form(...),
                  config=Depends(use_config)):
    """
    Expects cookie ``g_csrf_token`` to be set.
    Expects configuration ``google.client_id`` and ``google.certs_path`` to be set.
    """
    cookies = parse_cookie_header(request.headers.get("cookie"))
    cookie_g_csrf_token = cookies.get("g_csrf_token")
    if not g_csrf_token or cookie_g_csrf_token is None or cookie_g_csrf_token != g_csrf_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    id_info = jwt.decode(credential,
                         certs=config.app.google.certs,
                         audience=config.app.google.client_id)
    if id_info is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return "/"
