from configparser import ConfigParser
from hashlib import sha256


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

