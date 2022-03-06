from json import JSONDecodeError

from aiohttp import web
import logging
import traceback

from screfinery.auth import routes as auth_routes
from screfinery.storage import ore_validate, \
    station_validate, method_validate, InvalidDataError, StationStore, \
    UserStore, UserSessionStore, OreStore, MethodStore, UserPermStore

from screfinery.util import parse_args, configure_app, json_dumps
from screfinery import google_signin
from screfinery.resourcehandler import ResourceHandler, RelResourceHandler

log = logging.getLogger()
routes = web.RouteTableDef()


@routes.get("/api/hello")
async def hello(request):
    return web.Response(text="hello!")


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
        status_code = response.status
    except web.HTTPException as ex:
        raise
    except InvalidDataError as ex:
        message = {
            "status": "invalid",
            "invalid": ex.errors
        }
        status_code = 400
    except JSONDecodeError as ex:
        message = {
            "status": "error",
            "error": f"{type(ex).__name__}: {ex}"
        }
        status_code = 400
    except Exception as ex:
        message = {
            "status": "error",
            "error": f"{type(ex).__name__}: {ex}",
            "traceback": [it.strip() for it in traceback.format_tb(ex.__traceback__)]
        }
        status_code = 500

    return web.json_response(message, status=status_code, dumps=json_dumps)


async def init_app(args):
    app = web.Application(middlewares=[error_middleware])
    await configure_app(app, args)
    app.add_routes(routes)
    app.add_routes(google_signin.routes)
    app.add_routes(auth_routes)
    app.add_routes(
        ResourceHandler.factory("/api/user", UserStore())
    )
    app.add_routes(
        RelResourceHandler.factory("/api/user_session", UserSessionStore())
    )
    app.add_routes(
        RelResourceHandler.factory("/api/user_perm", UserPermStore())
    )
    app.add_routes(
        ResourceHandler.factory("/api/station", StationStore(), station_validate)
    )
    app.add_routes(
        ResourceHandler.factory("/api/ore", OreStore())
    )
    app.add_routes(
        ResourceHandler.factory("/api/method", MethodStore())
    )
    return app


if __name__ == "__main__":
    import logging.config
    args = parse_args()
    logging.config.fileConfig(args.config_path, disable_existing_loggers=False)
    web.run_app(init_app(args))
