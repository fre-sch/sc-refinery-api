import logging
from hashlib import sha256
from time import time

from aiohttp import web

from screfinery.storage import UserSessionStore, UserStore, UserPermStore
from screfinery.util import parse_cookie_header, json_dumps
from random import randint

log = logging.getLogger("screfinery.auth")
routes = web.RouteTableDef()

user_session_store = UserSessionStore()
user_store = UserStore()
user_perm_store = UserPermStore()


def mk_user_session_hash(user_id, user_ip, salt):
    hash_value = f"{user_id}/{user_ip}/{salt}"
    log.debug(f"mk_user_session_hash hash_value: {hash_value}")
    return sha256(hash_value.encode("utf-8")).hexdigest()


def request_session_vars(request):
    log.debug(request.headers.keys())
    cookies = parse_cookie_header(request.headers.get("cookie"))
    user_session_hash = cookies.get("s")
    user_id = cookies.get("u")
    user_ip = request.remote
    return user_id, user_ip, user_session_hash


async def check_request_session(request):
    try:
        return request.app["user_id"]
    except KeyError:
        pass

    user_id, user_ip, user_session_hash = request_session_vars(request)
    if user_session_hash is None or user_id is None:
        log.warning(f"missing session vars: user_id:{user_id}"
                    f", user_ip:{user_ip}"
                    f", user_session_hash:{user_session_hash}")
        raise web.HTTPForbidden()

    db = request.app["db"]
    db_session = await user_session_store.find_one(
        db, user_session_store.table.user_id == user_id)

    if db_session is None:
        log.warning("missing db session")
        raise web.HTTPUnauthorized()

    server_session_hash = mk_user_session_hash(
        db_session["user_id"], db_session["user_ip"], db_session["salt"])
    user_session_hash_check = mk_user_session_hash(
        user_id, user_ip, db_session["salt"])
    log.debug(f"server_session_hash: {server_session_hash}")
    log.debug(f"user_session_hash_check: {user_session_hash_check}")
    log.debug(f"user_session_hash: {user_session_hash}")
    is_valid_session = (
        server_session_hash
        == user_session_hash_check
        == user_session_hash
    )
    if not is_valid_session:
        log.warning("session hash invalid")
        raise web.HTTPUnauthorized()
    return user_id


async def check_user_perm(request, scope):
    user_id = await check_request_session(request)
    db = request.app["db"]
    _, user_perms = await user_perm_store.find_all(db, user_perm_store.table.user_id == user_id, limit=-1)
    user_scopes = set(it["scope"] for it in user_perms)
    log.debug(f"check user perms: '{scope}' in {user_scopes}")
    if scope not in user_scopes:
        raise web.HTTPUnauthorized()


@routes.post("/api/login")
async def handle_login(request):
    body = await request.post()
    user_mail = body.get("user_mail")
    # user_password = body.get("user_password")
    if user_mail is None:
        raise web.HTTPUnauthorized()
    db = request.app["db"]
    user = await user_store.find_one(db, user_store.table.mail == user_mail)
    if user is None:
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
    await user_session_store.remove_all(db, user_session_store.table.user_id == user["id"])
    await user_session_store.create(db, user_session)
    response = web.json_response(user, dumps=json_dumps)
    response.set_cookie("u", user["id"], path="/", max_age=60 * 60 * 24)
    response.set_cookie("s", server_session_hash, path="/",
                        max_age=60 * 60 * 24)
    return response
