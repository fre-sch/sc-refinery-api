import logging
from fnmatch import fnmatch
from hashlib import sha256
from typing import List

from screfinery.stores.model import User

log = logging.getLogger("screfinery")


def parse_dict_str(value: str, itemsep=";", kvsep=":") -> dict:
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
