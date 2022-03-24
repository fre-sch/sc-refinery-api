import logging
from collections import OrderedDict

from pypika import Query, functions as func, Order

log = logging.getLogger(__name__)


def group_rows(init_fn, *grouping_fns):
    def _group_rows(rows):
        groups = OrderedDict()
        for row in rows:
            group = init_fn(groups, row)
            for fn in grouping_fns:
                fn(group, row)
        return list(groups.values())
    return _group_rows


def group_init(id_fn, *keys):
    def _group_init(groups, row):
        row_id = id_fn(row)
        groups.setdefault(row_id, dict()).update(
            (key, row[key]) for key in keys
        )
        return groups[row_id]
    return _group_init


def group_rel_many_scalar(group_key, key):
    def _group_rel_many_scalar(group: dict, row: dict):
        value = row[key]
        group_value = group.setdefault(group_key, list())
        if value is None:
            return
        group_value.append(row[key])
    return _group_rel_many_scalar


def group_rel_one(group_key, *keys):
    def _group_rel_one(group: dict, row: dict):
        value = {key: row[key] for key in keys if row[key] is not None}
        group[group_key] = value
    return _group_rel_one


def group_rel_many(group_key, *keys):
    def _group_rel_many(group: dict, row: dict):
        value = {key: row[key] for key in keys}
        group_value = group.setdefault(group_key, list())
        if all(row[key] is None for key in keys):
            return
        group_value.append(value)
    return _group_rel_many


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

    def apply_sort(self, query, sort):
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
        query = self.apply_sort(query, sort)
        query_str = str(query)
        log.debug(f"BaseStore.find_all {query_str}")
        items = []
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                items.append(row)
        return total_count, items

    async def find_id(self, db, resource_id):
        return await self.find_one(db, self.primary_key == resource_id)

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

    async def query_rows_grouped(self, db, query_str, group_fn):
        async with db.execute(query_str) as cursor:
            rows = await cursor.fetchall()
        items = group_fn(rows)
        return items
