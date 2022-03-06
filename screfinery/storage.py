from jsonschema import Draft7Validator
from pypika import Table

from screfinery.basestore import BaseStore


User = Table("user")
UserSession = Table("user_session")
UserPerm = Table("user_perm")
Station = Table("station")
Ore = Table("ore")
Method = Table("method")
MethodOre = Table("method_ore")
MiningSession = Table("mining_session")


class UserSessionStore(BaseStore):
    def __init__(self):
        super().__init__(UserSession)


class UserStore(BaseStore):
    def __init__(self):
        super().__init__(User)


class UserPermStore(BaseStore):
    def __init__(self):
        super().__init__(UserPerm)

    @property
    def primary_key(self):
        return self.table.user_id


class StationStore(BaseStore):
    def __init__(self):
        super().__init__(Station)


class OreStore(BaseStore):
    def __init__(self):
        super().__init__(Ore)


class MethodStore(BaseStore):
    def __init__(self):
        super().__init__(Method)


class MiningSessionStore(BaseStore):
    def __init__(self):
        super().__init__(MiningSession)


class InvalidDataError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


def _resource_validator(resource_name, validator_spec):
    def resource_validator(data, case):
        validator = validator_spec.get(case)
        if validator is not None:
            errors = list(validator.iter_errors(data))
            if errors:
                raise InvalidDataError(f"{resource_name} data not valid", errors)
        data.pop("created", None)
        data.pop("updated", None)
        data.pop("id", None)
        return data
    return resource_validator


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
