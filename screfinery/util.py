import logging
from fnmatch import fnmatch
from hashlib import sha256
from typing import List

from sqlalchemy import and_

from screfinery.stores.model import User

log = logging.getLogger("screfinery")


def parse_dict_str(value: str, itemsep=";", kvsep=":") -> dict:
    if not value:
        return dict()

    items = value.split(itemsep)

    def _kv():
        for item in items:
            pairs = item.split(kvsep, maxsplit=1)
            yield pairs[0], first(pairs[1:], None)

    return dict(_kv())


def first(iterable, default=None):
    return next(iter(iterable), default)


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


def hash_password(salt, value):
    hash_value = f"{salt}/{value}"
    return sha256(hash_value.encode("utf-8")).hexdigest()


def is_authorized(scopes: List[str], required_scope: str) -> bool:
    return any(
        fnmatch(required_scope, scope)
        for scope in scopes
    )


def is_user_authorized(user: User, required_scope: str) -> bool:
    user_scopes = [it.scope for it in user.scopes]
    return is_authorized(user_scopes, required_scope)


class obj:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


def sa_filter_from_dict(model, filter_: dict):
    return and_(True, *(
        getattr(model, key).ilike(f"{value}%")
        for key, value in filter_.items()
        if hasattr(model, key)
    ))


def sa_order_by_from_dict(model, sort: dict):
    return [
        getattr(model, key).desc()
        if dir == "desc"
        else getattr(model, key).asc()
        for key, dir in sort.items()
        if hasattr(model, key)
    ]


def format_validation_errors(validation_errors):
    """
    Reformat pydantic ValidationError list
    """
    return [
        {
            "path": "/" + "/".join(str(it) for it in e["loc"][1:]),
            "message": e["msg"],
            "type": e["type"]
        }
        for e in validation_errors
    ]


def optint(value, default=0):
    try:
        return int(value)
    except:
        return default