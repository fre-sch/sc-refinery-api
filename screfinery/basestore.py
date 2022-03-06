import logging

from pypika import Table, Query, functions as func


log = logging.getLogger("screfinery.basestore")


class BaseStore:
    def __init__(self, table_name):
        self.table_name = table_name
        self.table = Table(self.table_name)

    @property
    def primary_key(self):
        return self.table.id

    async def find_one(self, db, criteria):
        query_str = str(
            Query.from_(self.table)
                .select("*")
                .where(criteria)
                .limit(1)
        )
        log.debug(f"BaseStore.find_one {query_str}")
        async with db.execute(query_str) as cursor:
            return await cursor.fetchone()

    async def find_all(self, db, criteria, offset=0, limit=10):
        query_str = str(
            Query.from_(self.table)
                .select(func.Count("*"))
                .where(criteria)
        )
        async with db.execute(query_str) as cursor:
            row = await cursor.fetchone()
            total_count = row[0]

        query_str = str(
            Query.from_(self.table)
                .select("*")
                .where(criteria)
                .offset(offset)
                .limit(limit)
        )
        log.debug(f"BaseStore.find_all {query_str}")
        items = []
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                items.append(row)
        return total_count, items

    async def find_id(self, db, resource_id):
        query_str = str(
            Query.from_(self.table)
                .select("*")
                .where(self.primary_key == resource_id)
                .limit(1)
        )
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
        return await self.find_id(db, resource_id)

    async def update_id(self, db, resource_id, data):
        query = Query.update(self.table).where(self.primary_key == resource_id)
        for key, value in data.items():
            query = query.set(key, value)
        query_str = str(query)
        log.debug(f"BaseStore.update_id {query_str}")
        await db.execute(query_str)
        await db.commit()
        return await self.find_id(db, resource_id)

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
