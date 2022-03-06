from jsonschema import Draft7Validator

from screfinery.basestore import BaseStore


class UserSessionStore(BaseStore):
    def __init__(self):
        super().__init__("user_session")


class UserStore(BaseStore):
    def __init__(self):
        super().__init__("user")


class UserPermStore(BaseStore):
    def __init__(self):
        super().__init__("user_perm")

    @property
    def primary_key(self):
        return self.table.user_id


class StationStore(BaseStore):
    def __init__(self):
        super().__init__("station")


class OreStore(BaseStore):
    def __init__(self):
        super().__init__("ore")


class MethodStore(BaseStore):
    def __init__(self):
        super().__init__("method")


class MiningSessionStore(BaseStore):
    def __init__(self):
        super().__init__("mining_session")


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
