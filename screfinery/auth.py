import logging
from time import time

from aiohttp import web
from pypika import Criterion

from screfinery import storage
from screfinery.util import parse_cookie_header, json_dumps, hash_password, \
    mk_user_session_hash
from random import randint


log = logging.getLogger("screfinery.auth")
routes = web.RouteTableDef()
user_session_store = storage.UserSessionStore()
user_store = storage.UserStore()
user_perm_store = storage.UserPermStore()


def request_session_vars(request):
    log.debug(request.headers.keys())
    cookies = parse_cookie_header(request.headers.get("cookie"))
    user_session_hash = cookies.get("s")
    user_id = cookies.get("u")
    user_ip = request.remote
    return user_id, user_ip, user_session_hash


async def check_request_session(request):
    user_id, user_ip, user_session_hash = request_session_vars(request)
    if user_session_hash is None or user_id is None:
        log.warning(f"missing session vars: user_id:{user_id}"
                    f", user_ip:{user_ip}"
                    f", user_session_hash:{user_session_hash}")
        raise web.HTTPForbidden()

    db = request.app["db"]
    db_session = await user_session_store.find_one(
        db, storage.UserSession.user_id == user_id)

    if db_session is None:
        log.warning(f"missing db session for user_id: {user_id}")
        raise web.HTTPUnauthorized()

    server_session_hash = mk_user_session_hash(
        db_session["user_id"], db_session["user_ip"], db_session["salt"])
    user_session_hash_check = mk_user_session_hash(
        user_id, user_ip, db_session["salt"])
    log.debug(f"server_session_hash: {server_session_hash}"
              f", user_session_hash_check: {user_session_hash_check}"
              f", user_session_hash: {user_session_hash}")
    is_valid_session = (
        server_session_hash
        == user_session_hash_check
        == user_session_hash
    )
    if not is_valid_session:
        log.warning(f"session hash invalid for user_id: {db_session['user_id']}")
        raise web.HTTPUnauthorized()
    return user_id


async def check_user_perm(request, scope):
    user_id = await check_request_session(request)
    db = request.app["db"]
    _, user_perms = await user_perm_store.find_all(
        db, storage.UserPerm.user_id == user_id, limit=-1)
    user_scopes = set(it["scope"] for it in user_perms)
    log.debug(f"check user perms: '{scope}' in {user_scopes}")
    if "*" in user_scopes:
        return
    if scope not in user_scopes:
        raise web.HTTPUnauthorized()


@routes.post("/login")
async def handle_login(request):
    body = await request.json()
    storage.login_validator(None, body, "login")
    password_hash = hash_password(
        request.app["config"]["main"]["password_salt"],
        body["password"])
    db = request.app["db"]
    user = await user_store.find_one(
        db,
        Criterion.all([
            storage.User.mail == body["username"],
            storage.User.password_hash == password_hash
        ]))
    if user is None:
        log.warning(f"failed login attempt: {body['username']}")
        raise web.HTTPUnauthorized()

    user_session = dict(
        user_id=user["id"],
        user_ip=request.remote,
        salt=int(time()) ^ randint(0, 2**32)
    )
    server_session_hash = mk_user_session_hash(
        user_session["user_id"], user_session["user_ip"], user_session["salt"]
    )
    log.debug(f"new session hash: {server_session_hash}")
    await user_session_store.remove_all(db, storage.UserSession.user_id == user["id"])
    await user_session_store.create(db, user_session)
    response = web.json_response(user, dumps=json_dumps)
    response.set_cookie("u", user["id"], path="/", max_age=60 * 60 * 24)
    response.set_cookie("s", server_session_hash, path="/",
                        max_age=60 * 60 * 24)
    return response


@routes.post("/login_session")
async def handle_login_session(request):
    user_id = await check_request_session(request)
    user = await user_store.find_id(request.app["db"], user_id)
    user_session = await user_session_store.find_one(
        request.app["db"],
        storage.UserSession.user_id == user_id
    )
    server_session_hash = mk_user_session_hash(
        user_session["user_id"], user_session["user_ip"], user_session["salt"]
    )
    response = web.json_response(user, dumps=json_dumps)
    response.set_cookie("u", user["id"], path="/", max_age=60 * 60 * 24)
    response.set_cookie("s", server_session_hash, path="/",
                        max_age=60 * 60 * 24)
    return response
