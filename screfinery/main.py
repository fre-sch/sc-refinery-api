from fastapi import FastAPI
from pydantic import ValidationError
from starlette.requests import Request

from screfinery import db
from screfinery.errors import IntegrityError
from screfinery.routes.user import user_routes
from screfinery.routes.station import station_routes
from screfinery.routes.ore import ore_routes
from screfinery.routes.method import method_routes
from screfinery.routes.mining_session import mining_session_routes
from screfinery.routes.auth import auth_routes

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import os

from screfinery.config import load_config

app = FastAPI(
    title="SC Refinery",
    description="API for SC Refinery app, a web app for managing team mining "
                " in Star Citizen.",
    version="0.1.0",
)

app.include_router(user_routes)
app.include_router(station_routes)
app.include_router(ore_routes)
app.include_router(method_routes)
app.include_router(mining_session_routes)
app.include_router(auth_routes)


@app.on_event("startup")
async def startup():
    config_path = os.environ["CONFIG_PATH"]
    app.state.config = load_config(config_path)
    engine, SessionLocal = db.init(app.state.config.app)
    app.state.db_engine = engine
    app.state.db_session = SessionLocal


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