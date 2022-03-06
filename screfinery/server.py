from json import JSONDecodeError

from aiohttp import web
import logging
import traceback

from pypika import Query, Table

from screfinery.auth import routes as auth_routes
from screfinery import storage

from screfinery.util import parse_args, configure_app, json_dumps
from screfinery import google_signin
from screfinery.resourcehandler import ResourceHandler, RelResourceHandler

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
    query = str(Query.from_(storage.Station).select("*"))
    async with db.execute(query) as cursor:
        async for row in cursor:
            result["stations"].append(row)

    query = str(Query.from_(storage.Ore).select("*"))
    async with db.execute(query) as cursor:
        async for row in cursor:
            result["ores"].append(row)

    query = str(
        Query.from_(storage.Method)
        .select(
            storage.Method.id.as_("method_id"),
            storage.Method.name.as_("method_name"),
            storage.Ore.id.as_("ore_id"),
            storage.Ore.name.as_("ore_name"),
            storage.MethodOre.efficiency.as_("method_efficiency"),
            storage.MethodOre.cost.as_("method_cost")
        )
        .left_join(storage.MethodOre)
        .on(storage.MethodOre.method_id == storage.Method.id)
        .left_join(storage.Ore)
        .on(storage.MethodOre.ore_id == storage.Ore.id)
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
    except storage.InvalidDataError as ex:
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
        ResourceHandler.factory("/api/user", storage.UserStore())
    )
    app.add_routes(
        RelResourceHandler.factory("/api/user_session", storage.UserSessionStore(), rel_column="user_id")
    )
    app.add_routes(
        RelResourceHandler.factory("/api/user_perm", storage.UserPermStore(), rel_column="user_id")
    )
    app.add_routes(
        ResourceHandler.factory("/api/station", storage.StationStore(), storage.station_validate)
    )
    app.add_routes(
        ResourceHandler.factory("/api/ore", storage.OreStore())
    )
    app.add_routes(
        ResourceHandler.factory("/api/method", storage.MethodStore())
    )
    return app


if __name__ == "__main__":
    import logging.config
    args = parse_args()
    logging.config.fileConfig(args.config_path, disable_existing_loggers=False)
    web.run_app(init_app(args))
