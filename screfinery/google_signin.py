from aiohttp import web
from google.auth import jwt
from screfinery.util import parse_cookie_header


routes = web.RouteTableDef()


@routes.post("/api/signin")
async def signin(request):
    config = request.app["config"]
    google_certs = request.app["google_certs"]
    post_body = await request.post()
    cookies = parse_cookie_header(request.headers.get("cookie"))
    csrf_check(
        cookies.get("g_csrf_token"),
        post_body.get("g_csrf_token")
    )
    id_token = post_body["credential"]
    id_info = jwt.decode(id_token,
                         certs=google_certs,
                         audience=config["google"]["client_id"])
    if id_info is None:
        raise web.HTTPUnauthorized()
    raise web.HTTPFound("/")


def csrf_check(cookie, body):
    if not cookie:
        raise web.HTTPBadRequest(text="expected cookie `g_csrf_token`")
    if not body:
        raise web.HTTPBadRequest(text="expected post data `g_csrf_token`")
    if cookie != body:
        raise web.HTTPBadRequest(text="csrf verification failed")