import logging
from datetime import datetime

from jsonschema import Draft7Validator
from pypika import Query, functions as fn

from screfinery.basestore import BaseStore, scalar_group
from screfinery.storage.table import User, UserPerm, DateTime
from screfinery.util import first, hash_password
from screfinery.validation import InvalidDataError, schema_validate, \
    _resource_validator


log = logging.getLogger("screfinery.storage")


class UserStore(BaseStore):
    def __init__(self):
        super().__init__(User)

    row_keys = ("id", "name", "mail", "is_active", "is_google", "created", "updated", "last_login")
    row_groups = (
        ("scopes", scalar_group("scope"), ),
    )

    async def find_one(self, db, criteria):
        query = (
            Query.from_(self.table)
            .select(
                User.star,
                UserPerm.scope
            )
            .left_join(UserPerm)
            .on(UserPerm.user_id == User.id)
            .where(criteria)
        )
        query_str = str(query)
        log.debug(f"UserStore.find_one {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_keys, self.row_groups)
        return first(items)

    async def find_all(self, db, criteria=None, sort=None, offset=0, limit=10):
        total_count = await self.count_by(db, criteria)
        user_query = (
            Query.from_(User)
            .select(
                User.id,
                User.mail,
                User.name,
                User.is_active,
                User.is_google,
                User.created,
                User.updated,
                User.last_login
            )
            .where(criteria)
            .offset(offset)
            .limit(limit)
        )
        user_alias = user_query.as_("user")
        query = (
            Query.from_(user_alias)
            .left_join(UserPerm)
            .on(user_alias.id == UserPerm.user_id)
            .select(
                User.id,
                User.mail,
                User.name,
                User.is_active,
                User.is_google,
                DateTime(User.created).as_("created"),
                DateTime(User.updated).as_("updated"),
                DateTime(User.last_login).as_("last_login"),
                UserPerm.scope
            )
            .where(criteria)
        )
        query = self.appy_sort(query, sort)
        query_str = str(query)
        log.debug(f"BaseStore.find_all {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_keys, self.row_groups)
        return total_count, items

    async def update_scopes(self, db, resource_id, scopes):
        if not scopes:
            return
        query_str = str(
            Query.from_(UserPerm).delete()
            .where(UserPerm.user_id == resource_id)
        )
        log.debug(f"UserStore.update_scopes {query_str}")
        await db.execute(query_str)
        query_str = str(
            Query.into(UserPerm)
            .columns([UserPerm.user_id, UserPerm.scope])
            .insert(*[
                (resource_id, scope) for scope in scopes
            ])
        )
        log.debug(f"UserStore.update_scopes {query_str}")
        await db.execute(query_str)
        await db.commit()

    async def update_id(self, db, resource_id, data):
        data.pop("created", None)
        data["updated"] = datetime.now()
        scopes = data.pop("scopes", [])
        await self.update_scopes(db, resource_id, scopes)
        return await super().update_id(db, resource_id, data)

    async def create(self, db, data):
        scopes = data.pop("scopes", [])
        keys = []
        values = []
        for key, value in data.items():
            keys.append(key)
            values.append(value)
        query_str = str(
            Query.into(self.table)
            .columns(keys)
            .insert(values)
        )
        log.debug(f"UserStore.create {query_str}")
        async with db.execute(query_str) as cursor:
            resource_id = cursor.lastrowid
            await db.commit()
            await self.update_scopes(db, resource_id, scopes)

        resource = await self.find_id(db, resource_id)
        return resource

    async def remove_id(self, db, resource_id):
        query_str = str(
            Query.from_(UserPerm)
            .delete()
            .where(UserPerm.user_id == resource_id)
        )
        log.debug(f"UserStore.remove_id {query_str}")
        await db.execute(query_str)
        await db.commit()
        return await super().remove_id(db, resource_id)


def user_validate_password(salt, data):
    if "password" in data and "password_confirm" not in data:
        message = "expected properties `password` and `password_confirm`, `password_confirm` missing"
        raise InvalidDataError(
            message,
            errors=[
                {
                    "message": message,
                    "path": "$.password_confirm"
                }
            ]
        )
    if "password_confirm" in data and not "password" in data:
        message = "expected properties `password` and `password_confirm`, `password` missing"
        raise InvalidDataError(
            message,
            errors=[
                {
                    "message": message,
                    "path": "$.password"
                }
            ]
        )

    if "password" in data:
        password_confirm_hash = hash_password(salt, data["password_confirm"])
        password_hash = hash_password(salt, data["password"])
        if password_confirm_hash != password_hash:
            raise InvalidDataError(
                "expected `password` to match `password_confirm`",
                errors=[
                    {
                        "message": "expected `password` to match `password_confirm`",
                        "path": "$.password_confirm"
                    }
                ]
            )
        data.pop("password")
        data.pop("password_confirm", None)
        data["password_hash"] = password_hash


def user_validator(config, data, case):
    if case == "create":
        schema_validate(Draft7Validator({
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1
                },
                "mail": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^.+@.+$",
                },
                "is_google": {
                    "type": "boolean"
                },
                "password": {
                    "type": "string",
                    "minLength": 1
                },
                "password_confirm": {
                    "type": "string",
                    "minLength": 1
                },
                "is_active": {
                    "type": "boolean"
                }
            },
            "required": ["name", "mail", "password", "password_confirm"]
        }), "user", data)
        password_salt = config["main"]["password_salt"]
        user_validate_password(password_salt, data)

    elif case == "update":
        schema_validate(Draft7Validator({
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1
                },
                "mail": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^.+@.+$",
                },
                "is_google": {
                    "type": "boolean"
                },
                "password": {
                    "type": ["string", "null"]
                },
                "password_confirm": {
                    "type": ["string", "null"]
                },
                "is_active": {
                    "type": "boolean"
                }
            }
        }), "user", data)
        password_salt = config["main"]["password_salt"]
        user_validate_password(password_salt, data)

    return data


login_validator = _resource_validator("login", {
    "login": Draft7Validator({
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "minLength": 1
            },
            "password": {
                "type": "string",
                "minLength": 1
            }
        },
        "required": ["username", "password"]
    })
})