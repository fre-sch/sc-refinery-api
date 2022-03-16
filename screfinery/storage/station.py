import logging

from jsonschema import Draft7Validator
from pypika import Query

from screfinery.basestore import BaseStore, item_group
from screfinery.storage.table import Station, StationOre, Ore
from screfinery.util import first
from screfinery.validation import _resource_validator


log = logging.getLogger("screfinery.storage")


class StationStore(BaseStore):
    def __init__(self):
        super().__init__(Station)

    row_keys = ("id", "name", "created", "updated")
    row_groups = (
        ("efficiency", item_group("ore_id", "ore_name", "efficiency_bonus"),),
    )

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
                StationOre.efficiency_bonus,
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
                StationOre.efficiency_bonus,
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

    async def update_efficiency(self, db, resource_id, values):
        if not values:
            return
        query_str = str(
            Query.from_(StationOre).delete()
            .where(StationOre.station_id == resource_id)
        )
        log.debug(f"StationStore.update_efficiency {query_str}")
        await db.execute(query_str)
        query_str = str(
            Query.into(StationOre)
            .columns([StationOre.station_id, StationOre.ore_id, StationOre.efficiency_bonus])
            .insert(*[
                (resource_id, it["ore_id"], it["efficiency_bonus"]) for it in values
            ])
        )
        log.debug(f"StationStore.update_efficiency {query_str}")
        await db.execute(query_str)
        await db.commit()

    async def update_id(self, db, resource_id, data):
        efficiency = data.pop("efficiency", [])
        await self.update_efficiency(db, resource_id, efficiency)
        return await super().update_id(db, resource_id, data)

    async def create(self, db, data):
        efficiency = data.pop("efficiency", [])
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
        log.debug(f"StationStore.create {query_str}")
        async with db.execute(query_str) as cursor:
            resource_id = cursor.lastrowid
            await db.commit()
            await self.update_efficiency(db, resource_id, efficiency)

        resource = await self.find_id(db, resource_id)
        return resource

    async def remove_id(self, db, resource_id):
        query_str = str(
            Query.from_(StationOre)
                .delete()
                .where(StationOre.station_id == resource_id)
        )
        log.debug(f"StationStore.remove_id {query_str}")
        await db.execute(query_str)
        await db.commit()
        return await super().remove_id(db, resource_id)


station_validate = _resource_validator("station", {
    "create": Draft7Validator({
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            },
            "efficiency": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ore_id": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "efficiency_bonus": {
                            "type": "number"
                        }
                    }
                },
                "required": [
                    "ore_id",
                    "efficiency_bonus"
                ]
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
            "efficiency": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ore_id": {
                            "type": "number",
                            "multipleOf": 1
                        },
                        "efficiency_bonus": {
                            "type": "number"
                        }
                    }
                },
                "required": [
                    "ore_id",
                    "efficiency_bonus"
                ]
            }
        },
        "required": []
    })
})