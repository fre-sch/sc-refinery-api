import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED
from google.auth import jwt

from screfinery import schema
from screfinery.dependency import use_db, use_config
from screfinery.stores import user_store
from screfinery.util import hash_password, parse_cookie_header

log = logging.getLogger(__name__)
ONE_DAY = 60 * 60 * 24
auth_routes = APIRouter()


@auth_routes.post("/login", response_model=schema.User, tags=["user"])
def login(request: Request,
          login: schema.Login,
          db: Session = Depends(use_db),
          config=Depends(use_config)) -> schema.User:
    """
    Given a username and password, create a user session and respond with user
    and cookies ``u`` (user's id) and ``s`` (session hash).
    """
    password_hash = hash_password(login.password, config.main.password_salt)
    user = user_store.find_by_credentials(db, login.username, password_hash)
    if user is None:
        raise HTTPException(status_code=401)

    user_session, session_hash = user_store.create_session(db, user, request.client.host)
    response = JSONResponse(
        status_code=200,
        content=jsonable_encoder(schema.User.from_orm(user))
    )
    response.set_cookie("u", user.id, path="/", max_age=ONE_DAY)
    response.set_cookie("s", session_hash, path="/", max_age=ONE_DAY)
    return response


@auth_routes.post("/google_signin", tags=["user"])
def google_signin(request: Request,
                  g_csrf_token: Form(...),
                  credential: Form(...),
                  config: Depends(use_config)):
    cookies = parse_cookie_header(request.headers.get("cookie"))
    cookie_g_csrf_token = cookies.get("g_csrf_token")
    if not g_csrf_token or cookie_g_csrf_token is None or cookie_g_csrf_token != g_csrf_token:
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    id_info = jwt.decode(credential,
                         certs=config.app.google.certs,
                         audience=config.app.google.client_id)
    if id_info is None:
        raise HTTPException(HTTP_401_UNAUTHORIZED)
    # redirect "/"
