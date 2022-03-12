import json
import logging
from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from configparser import ConfigParser

import aiosqlite
from jsonschema import ValidationError


log = logging.getLogger("screfinery.util")


def parse_cookie_header(value):
    """
    http.cookies.SimpleCookie fails to correctly parse google's cookie
    """
    if value is None:
        return dict()
    return dict(
        it.strip().split("=", 1)
        for it in value.split(";")
    )


def parse_args():
    arg_parser = ArgumentParser(description="screfinery")
    arg_parser.add_argument("config_path", type=Path)
    return arg_parser.parse_args()


def load_config(path):
    config = ConfigParser()
    config.read(path)
    return config


def load_google_certs(path):
    with open(path, "r") as fp:
        return json.load(fp)


async def init_sqlite_db(app):
    db_path = app["config"]["sqlite"]["db_path"]
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    app["db"] = db
    yield
    await db.close()


async def configure_app(app, args):
    app["config"] = load_config(args.config_path)
    app["google_certs"] = load_google_certs(
        app["config"]["google"]["certs_path"])
    use_db = app["config"]["main"].get("use_db")
    if use_db == "sqlite":
        app.cleanup_ctx.append(init_sqlite_db)
    else:
        raise NotImplementedError(f"{use_db} not implemented")


def first(itr):
    return next(iter(itr), None)


def json_convert(value):
    if isinstance(value, aiosqlite.Row):
        return dict(value)
    if isinstance(value, ValidationError):
        return dict(
            message=value.message,
            path=value.json_path
        )
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"json_convert cannot convert {value}: {type(value)}")


json_dumps = partial(json.dumps, default=json_convert)


def hash_password(salt, value):
    hash_value = f"{salt}/{value}"
    return sha256(hash_value.encode("utf-8")).hexdigest()


def mk_user_session_hash(user_id, user_ip, salt):
    hash_value = f"{user_id}/{user_ip}/{salt}"
    return sha256(hash_value.encode("utf-8")).hexdigest()