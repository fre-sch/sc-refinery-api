"""
## API for SC Refinery app, a web app for managing team mining in Star Citizen.

Requests require successful authorization using /login and appropriate permissions.

Permissions are based on resource name and action. For example to list all
``station`` or fetch one ``station``, permission ``station.read`` is required.

Additionally, some resources are _owned_ by a user. The user owning these
resources always has full access to them.

Actions are: ``read``, ``create``, ``update``, ``delete``.

In place of a resource or action, wildcard ``*`` can be used like: ``*`` to
give full access to everything, ``user.*`` to all access to just the resource
``user``, ``*.read`` to allow read access to all resources.

"""
import logging
import os

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import ALL_METHODS, SAFELISTED_HEADERS
from pydantic import ValidationError

from screfinery import db, version
from screfinery.config import load_config, CorsConfig
from screfinery.errors import IntegrityError
from screfinery.routes.auth import auth_routes
from screfinery.routes.method import method_routes
from screfinery.routes.mining_session import mining_session_routes
from screfinery.routes.ore import ore_routes
from screfinery.routes.station import station_routes
from screfinery.routes.user import user_routes


log = logging.getLogger("screfinery")
app = FastAPI(
    title="SC Refinery",
    description=__doc__,
    version=version.version
)


@app.route("/version", methods=["GET"])
def get_version(request: Request):
    return JSONResponse(content=version.version)


@app.on_event("startup")
async def startup():
    config_path = os.environ["CONFIG_PATH"]
    config = load_config(config_path)
    is_env_dev = config.env == "dev"
    app.state.config = config
    app.debug = is_env_dev
    engine, session_maker = db.init(config.app.db, is_env_dev)
    app.state.db_engine = engine
    app.state.db_session = session_maker

    for route in app.routes:
        log.debug(f"{','.join(route.methods)} {route.path}")


@app.exception_handler(ValidationError)
def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({
            "status": "invalid",
            "invalid": exc.errors()
        })
    )


@app.exception_handler(IntegrityError)
def handle_integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({
            "status": "invalid",
            "invalid": str(exc)
        })
    )


def _add_cors_headers(headers, origin=None):
    headers['Access-Control-Allow-Origin'] = "*" if origin is None else origin
    headers['Access-Control-Allow-Methods'] = ", ".join(ALL_METHODS)
    headers['Access-Control-Allow-Headers'] = ", ".join(SAFELISTED_HEADERS)
    headers["Access-Control-Expose-Headers"] = ", ".join(SAFELISTED_HEADERS)
    headers["Access-Control-Allow-Credentials"] = "true"


@app.options('/{rest_of_path:path}')
async def preflight_handler(request: Request, rest_of_path: str) -> Response:
    response = Response()
    _add_cors_headers(response.headers, request.headers.get("origin"))
    return response


@app.middleware("http")
async def add_CORS_header(request: Request, call_next):
    # set CORS headers
    response = await call_next(request)
    _add_cors_headers(response.headers, request.headers.get("origin"))
    return response


app.include_router(user_routes)
app.include_router(station_routes)
app.include_router(ore_routes)
app.include_router(method_routes)
app.include_router(mining_session_routes)
app.include_router(auth_routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

