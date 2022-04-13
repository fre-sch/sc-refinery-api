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

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
app.include_router(user_routes)
app.include_router(station_routes)
app.include_router(ore_routes)
app.include_router(method_routes)
app.include_router(mining_session_routes)
app.include_router(auth_routes)


@app.route("/version", methods=["GET"])
def get_version(request: Request):
    return JSONResponse(content=version.version)


@app.on_event("startup")
async def startup():
    config_path = os.environ["CONFIG_PATH"]
    config = load_config(config_path)
    app.state.config = config
    app.debug = app.state.config.env == "dev"

    _configure_cors(app, config.app.cors)
    _configure_db(app, config.app.db, config.env == "dev")

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


def _configure_db(app: FastAPI, config: dict, debug: bool):
    engine, session_maker = db.init(config, debug)
    app.state.db_engine = engine
    app.state.db_session = session_maker


def _configure_cors(app: FastAPI, config: CorsConfig):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allow_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )