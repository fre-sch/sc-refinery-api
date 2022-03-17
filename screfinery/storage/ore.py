from jsonschema import Draft7Validator

from screfinery.basestore import BaseStore
from screfinery.storage.table import Ore
from screfinery.validation import _resource_validator


class OreStore(BaseStore):
    def __init__(self):
        super().__init__(Ore)


ore_validate = _resource_validator("ore", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        },
        "required": ["name"]
    }),
    "update": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            }
        }
    })
})