import logging

from jsonschema import Draft7Validator
from pypika import Query

from screfinery.basestore import BaseStore, group_rel_many, group_rows, group_init
from screfinery.storage.table import Method, MethodOre, Ore
from screfinery.util import first
from screfinery.validation import _resource_validator


log = logging.getLogger("screfinery.storage")


class MethodStore(BaseStore):
    def __init__(self):
        super().__init__(Method)

    row_groups = staticmethod(group_rows(
        group_init(lambda row: row["id"], "id", "name", "created", "updated"),
        group_rel_many("ores", "ore_id", "ore_name", "efficiency", "cost", "duration"),
    ))

    async def find_one(self, db, criteria):
        query = (
            Query.from_(self.table)
            .left_join(MethodOre)
            .on(MethodOre.method_id == Method.id)
            .left_join(Ore)
            .on(MethodOre.ore_id == Ore.id)
            .select(
                Method.id,
                Method.name,
                Method.created,
                Method.updated,
                MethodOre.efficiency,
                MethodOre.cost,
                MethodOre.duration,
                Ore.id.as_("ore_id"),
                Ore.name.as_("ore_name")
            )
            .where(criteria)
        )
        query_str = str(query)
        log.debug(f"MethodStore.find_one {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_groups)
        return first(items)

    async def find_all(self, db, criteria=None, sort=None, offset=0, limit=10):
        total_count = await self.count_by(db, criteria)
        main_query = (
            Query.from_(Method)
            .select(Method.id, Method.name, Method.created, Method.updated)
            .where(criteria)
            .offset(offset)
            .limit(limit)
        )
        main_alias = main_query.as_("method")
        join_query = (
            Query.from_(main_alias)
            .left_join(MethodOre)
            .on(main_alias.id == MethodOre.method_id)
            .left_join(Ore)
            .on(MethodOre.ore_id == Ore.id)
            .select(
                Method.id,
                Method.name,
                Method.created,
                Method.updated,
                MethodOre.efficiency,
                MethodOre.cost,
                MethodOre.duration,
                Ore.id.as_("ore_id"),
                Ore.name.as_("ore_name")
            )
            .where(criteria)
        )
        join_query = self.apply_sort(join_query, sort)
        query_str = str(join_query)
        log.debug(f"MethodStore.find_all {query_str}")
        items = await self.query_rows_grouped(db, query_str, self.row_groups)
        return total_count, items

    async def update_ores(self, db, resource_id, values):
        if not values:
            return
        query_str = str(
            Query.from_(MethodOre).delete()
            .where(MethodOre.method_id == resource_id)
        )
        log.debug(f"MethodStore.update_efficiency {query_str}")
        await db.execute(query_str)
        query_str = str(
            Query.into(MethodOre)
            .columns([
                MethodOre.method_id,
                MethodOre.ore_id,
                MethodOre.efficiency,
                MethodOre.cost,
                MethodOre.duration,
            ])
            .insert(*[
                (
                    resource_id,
                    it["ore_id"],
                    it["efficiency"],
                    it["cost"],
                    it["duration"],
                )
                for it in values
            ])
        )
        log.debug(f"MethodStore.update_ores {query_str}")
        await db.execute(query_str)
        await db.commit()

    async def update_id(self, db, resource_id, data):
        relation_values = data.pop("ores", [])
        await self.update_ores(db, resource_id, relation_values)
        return await super().update_id(db, resource_id, data)

    async def create(self, db, data):
        efficiency = data.pop("ores", [])
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
        log.debug(f"MethodStore.create {query_str}")
        async with db.execute(query_str) as cursor:
            resource_id = cursor.lastrowid
            await db.commit()
            await self.update_ores(db, resource_id, efficiency)

        resource = await self.find_id(db, resource_id)
        return resource

    async def remove_id(self, db, resource_id):
        query_str = str(
            Query.from_(MethodOre)
            .delete()
            .where(MethodOre.method_id == resource_id)
        )
        log.debug(f"MethodStore.remove_id {query_str}")
        await db.execute(query_str)
        await db.commit()
        return await super().remove_id(db, resource_id)


method_validate = _resource_validator("method", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            },
            "ores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ore_id": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "efficiency": {
                            "type": "number"
                        },
                        "cost": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "duration": {
                            "type": "number",
                            "multipleOf": 1
                        }
                    },
                    "required": [
                        "ore_id",
                        "efficiency",
                        "cost",
                        "duration"
                    ]
                }
            }
        },
        "required": [
            "name"
        ]
    }),
    "update": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            },
            "ores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ore_id": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "efficiency": {
                            "type": "number"
                        },
                        "cost": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "duration": {
                            "type": "number",
                            "multipleOf": 1
                        }
                    },
                    "required": [
                        "ore_id",
                    ]
                }
            }
        }
    })
})