import logging
from collections import defaultdict
from pypika import Query, functions as func, Order

log = logging.getLogger("screfinery.basestore")


def scalar_group(key: str) -> callable:
    def inner(row):
        return row[key]
    return inner


def item_group(*keys) -> callable:
    def inner(row):
        has_values = any((key in row.keys() and row[key] is not None) for key in keys)
        if has_values:
            return {key: row[key] for key in keys}
    return inner


class BaseStore:
    def __init__(self, table):
        self.table = table

    @property
    def table_name(self):
        return self.table.name

    @property
    def primary_key(self):
        return self.table.id

    def find_one_query(self, criteria):
        return (
            Query.from_(self.table)
            .select("*")
            .where(criteria)
            .limit(1)
        )

    def appy_sort(self, query, sort):
        if sort is not None:
            for key, value in sort.items():
                sort_dir = Order.asc if value == "asc" else Order.desc
                query = query.orderby(key, order=sort_dir)
        return query

    async def find_one(self, db, criteria):
        query_str = str(self.find_one_query(criteria))
        log.debug(f"BaseStore.find_one {query_str}")
        async with db.execute(query_str) as cursor:
            resource = await cursor.fetchone()
            return resource

    async def find_all(self, db, criteria=None, sort=None, offset=0, limit=10):
        total_count = await self.count_by(db, criteria)
        query = (
            Query.from_(self.table)
                .select("*")
                .where(criteria)
                .offset(offset)
                .limit(limit)
        )
        query = self.appy_sort(query, sort)
        query_str = str(query)
        log.debug(f"BaseStore.find_all {query_str}")
        items = []
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                items.append(row)
        return total_count, items

    async def find_id(self, db, resource_id):
        query_str = str(self.find_one_query(
            self.primary_key == resource_id
        ))
        log.debug(f"BaseStore.find_id {query_str}")
        async with db.execute(query_str) as cursor:
            resource = await cursor.fetchone()
        return resource

    async def create(self, db, data):
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
        resource = await self.find_id(db, resource_id)
        return resource

    async def update_id(self, db, resource_id, data):
        query = Query.update(self.table).where(self.primary_key == resource_id)
        for key, value in data.items():
            query = query.set(key, value)
        query_str = str(query)
        log.debug(f"BaseStore.update_id {query_str}")
        await db.execute(query_str)
        await db.commit()
        resource = await self.find_id(db, resource_id)
        return resource

    async def remove_id(self, db, resource_id):
        query_str = str(
            Query.from_(self.table)
                .delete()
                .where(self.primary_key == resource_id)
        )
        log.debug(f"BaseStore.remove_id {query_str}")
        await db.execute(query_str)
        await db.commit()

    async def remove_all(self, db, criteria):
        query_str = str(
            Query.from_(self.table).delete().where(criteria)
        )
        log.debug(f"BaseStore.remove_all {query_str}")
        await db.execute(query_str)
        await db.commit()

    async def count_by(self, db, criteria):
        query_str = str(
            Query.from_(self.table)
                .select(func.Count("*"))
                .where(criteria)
        )
        log.debug(f"BaseStore.count_by {query_str}")
        async with db.execute(query_str) as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def query_rows_grouped(self, db, query_str, row_keys, group_keys):
        ids = list()
        values = defaultdict(dict)
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                if row["id"] not in ids:
                    ids.append(row["id"])
                values[row["id"]].update(
                    (key, row[key]) for key in row_keys
                )
                for item_key, group_fn in group_keys:
                    group = values[row["id"]].setdefault(item_key, [])
                    group_value = group_fn(row)
                    if group_value is not None:
                        group.append(group_value)
        items = [values[id] for id in ids]
        return items