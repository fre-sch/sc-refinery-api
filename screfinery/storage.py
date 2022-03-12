import logging

from jsonschema import Draft7Validator
from pypika import Table, Query

from screfinery.basestore import BaseStore, scalar_group, item_group
from screfinery.util import first, hash_password
from screfinery.validation import InvalidDataError, schema_validate, \
    _resource_validator

log = logging.getLogger("screfinery.storage")
User = Table("user")
UserSession = Table("user_session")
UserPerm = Table("user_perm")
Station = Table("station")
Ore = Table("ore")
Method = Table("method")
MethodOre = Table("method_ore")
StationOre = Table("station_ore")
MiningSession = Table("mining_session")


class UserSessionStore(BaseStore):
    def __init__(self):
        super().__init__(UserSession)


class UserStore(BaseStore):
    def __init__(self):
        super().__init__(User)

    row_keys = ("id", "name", "mail", "created", "updated")
    row_groups = (
        ("scopes", scalar_group("scope"), ),
    )

    async def find_id(self, db, resource_id):
        return await self.find_one(db, User.id == resource_id)

    async def find_one(self, db, criteria):
        query = (
            Query.from_(self.table)
                .select(User.star, UserPerm.scope)
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
            .select(User.id, User.mail, User.name, User.created, User.updated)
            .where(criteria)
            .offset(offset)
            .limit(limit)
        )
        user_alias = user_query.as_("user")
        query = (
            Query.from_(user_alias)
            .left_join(UserPerm)
            .on(user_alias.id == UserPerm.user_id)
            .select(User.id, User.mail, User.name, User.created, User.updated, UserPerm.scope)
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
        log.debug(f"BaseStore.create {query_str}")
        async with db.execute(query_str) as cursor:
            resource_id = cursor.lastrowid
            await db.commit()
            await self.update_scopes(db, resource_id, scopes)

        resource = await self.find_id(db, resource_id)
        return resource


class UserPermStore(BaseStore):
    def __init__(self):
        super().__init__(UserPerm)

    @property
    def primary_key(self):
        return self.table.user_id


class StationStore(BaseStore):
    def __init__(self):
        super().__init__(Station)

    row_keys = ("id", "name", "created", "updated")
    row_groups = (
        ("efficiency", item_group("ore_id", "ore_name", "bonus"),),
    )

    async def find_id(self, db, resource_id):
        return await self.find_one(db, Station.id == resource_id)

    async def find_one(self, db, criteria):
        query = (
            Query.from_(self.table)
            .left_join(StationOre)
            .on(StationOre.station_id == Station.id)
            .left_join(Ore)
            .on(StationOre.ore_id == Ore.id)
            .select(
                Station.id,
                Station.name,
                Station.created,
                Station.updated,
                StationOre.efficiency_bonus.as_("bonus"),
                Ore.id.as_("ore_id"),
                Ore.name.as_("ore_name")
            )
            .where(criteria)
        )
        query_str = str(query)
        log.debug(f"UserStore.find_one {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_keys, self.row_groups)
        return first(items)

    async def find_all(self, db, criteria=None, sort=None, offset=0, limit=10):
        total_count = await self.count_by(db, criteria)
        main_query = (
            Query.from_(Station)
            .select(Station.id, Station.name, Station.created, Station.updated)
            .where(criteria)
            .offset(offset)
            .limit(limit)
        )
        main_alias = main_query.as_("station")
        join_query = (
            Query.from_(main_alias)
            .left_join(StationOre)
            .on(main_alias.id == StationOre.station_id)
            .left_join(Ore)
            .on(StationOre.ore_id == Ore.id)
            .select(
                Station.id,
                Station.name,
                Station.created,
                Station.updated,
                StationOre.efficiency_bonus.as_("bonus"),
                Ore.id.as_("ore_id"),
                Ore.name.as_("ore_name")
            )
            .where(criteria)
        )
        join_query = self.appy_sort(join_query, sort)
        query_str = str(join_query)
        log.debug(f"BaseStore.find_all {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_keys, self.row_groups)
        return total_count, items
    #
    # async def update_scopes(self, db, resource_id, scopes):
    #     if not scopes:
    #         return
    #     query_str = str(
    #         Query.from_(UserPerm).delete()
    #         .where(UserPerm.user_id == resource_id)
    #     )
    #     log.debug(f"UserStore.update_scopes {query_str}")
    #     await db.execute(query_str)
    #     query_str = str(
    #         Query.into(UserPerm)
    #         .columns([UserPerm.user_id, UserPerm.scope])
    #         .insert(*[
    #             (resource_id, scope) for scope in scopes
    #         ])
    #     )
    #     log.debug(f"UserStore.update_scopes {query_str}")
    #     await db.execute(query_str)
    #     await db.commit()
    #
    # async def update_id(self, db, resource_id, data):
    #     scopes = data.pop("scopes", [])
    #     await self.update_scopes(db, resource_id, scopes)
    #     return await super().update_id(db, resource_id, data)


class OreStore(BaseStore):
    def __init__(self):
        super().__init__(Ore)


class MethodStore(BaseStore):
    def __init__(self):
        super().__init__(Method)


class MiningSessionStore(BaseStore):
    def __init__(self):
        super().__init__(MiningSession)


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
                }
            }
        }), "user", data)
        password_salt = config["main"]["password_salt"]
        user_validate_password(password_salt, data)

    return data


station_validate = _resource_validator("station", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False,
        "required": ["name"]
    }),
    "update": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False
    })
})
ore_validate = _resource_validator("ore", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False,
        "required": ["name"]
    }),
    "update": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False,
    })
})
method_validate = _resource_validator("method", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False,
        "required": ["name"]
    }),
    "update": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False
    })
})
