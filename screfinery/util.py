import json
import logging
from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from configparser import ConfigParser
from urllib.parse import urlparse

import aiosqlite
from jsonschema import ValidationError


log = logging.getLogger(__name__)


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


def db_connect(config):
    if "db" not in config:
        raise Exception("missing [db] section in config")

    db_url = config["db"].get("url")
    if not db_url:
        raise Exception("missing [db] url in config")

    if db_url.startswith("sqlite"):
        return sqlite_connect(db_url)

    raise NotImplementedError(f"`{db_url}` not implemented")


async def sqlite_connect(url):
    db_url = urlparse(url)
    db = await aiosqlite.connect(db_url.netloc)
    db.row_factory = aiosqlite.Row
    return db


def app_db_context(connect):
    async def inner(app):
        app["db"] = await connect
        yield
        await app["db"].close()
    return inner


async def configure_app(app, args):
    app["config"] = load_config(args.config_path)
    app["google_certs"] = load_google_certs(
        app["config"]["google"]["certs_path"])

    configured_db = db_connect(app["config"])
    app.cleanup_ctx.append(app_db_context(configured_db))


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