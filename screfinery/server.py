from json import JSONDecodeError

import aiohttp_cors
from aiohttp import web
import logging
import traceback

from pypika import Query

from screfinery import storage
from screfinery.storage import table
from screfinery.auth import routes as auth_routes
from screfinery.util import parse_args, configure_app, json_dumps
from screfinery import google_signin
from screfinery.resourcehandler import ResourceHandler, RelResourceHandler
from screfinery.validation import InvalidDataError

log = logging.getLogger()
routes = web.RouteTableDef()


@routes.get("/api/hello")
async def hello(request):
    return web.Response(text="hello!")


@routes.get("/api/init")
async def init(request):
    db = request.app["db"]
    result = {
        "stations": list(),
        "ores": list(),
        "methods": list()
    }
    query = str(Query.from_(table.Station).select("*"))
    async with db.execute(query) as cursor:
        async for row in cursor:
            result["stations"].append(row)

    query = str(Query.from_(table.Ore).select("*"))
    async with db.execute(query) as cursor:
        async for row in cursor:
            result["ores"].append(row)

    query = str(
        Query.from_(table.Method)
        .select(
            table.Method.id.as_("method_id"),
            table.Method.name.as_("method_name"),
            table.Ore.id.as_("ore_id"),
            table.Ore.name.as_("ore_name"),
            table.MethodOre.efficiency.as_("method_efficiency"),
            table.MethodOre.cost.as_("method_cost")
        )
        .left_join(table.MethodOre)
        .on(
            table.MethodOre.method_id == table.Method.id)
        .left_join(table.Ore)
        .on(
            table.MethodOre.ore_id == table.Ore.id)
    )
    log.debug(query)
    async with db.execute(query) as cursor:
        async for row in cursor:
            result["methods"].append(row)

    return web.json_response(result, dumps=json_dumps)


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
        ResourceHandler.factory("/user", storage.UserStore(), storage.user_validator)
    )
    app.add_routes(
        RelResourceHandler.factory("/user_session", storage.UserSessionStore(), rel_column="user_id")
    )
    app.add_routes(
        RelResourceHandler.factory("/user_perm", storage.UserPermStore(), rel_column="user_id")
    )
    app.add_routes(
        ResourceHandler.factory("/station", storage.StationStore(),
                                storage.station_validate)
    )
    app.add_routes(
        ResourceHandler.factory("/ore", storage.OreStore(), storage.ore_validate)
    )
    app.add_routes(
        ResourceHandler.factory("/method", storage.MethodStore(), storage.method_validate)
    )
    app.add_routes(
        ResourceHandler.factory("/mining_session", storage.MiningSessionStore(), storage.mining_session_validate)
    )
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    for route in list(app.router.routes()):
        if not isinstance(route.resource, web.StaticResource):  # <<< WORKAROUND
            cors.add(route)
    return app


if __name__ == "__main__":
    import logging.config
    args = parse_args()
    logging.config.fileConfig(args.config_path, disable_existing_loggers=False)
    web.run_app(init_app(args))
