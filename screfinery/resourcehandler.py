import logging

from aiohttp import web
from pypika import Query, functions as func

from screfinery.auth import check_user_perm
from screfinery.util import json_dumps


log = logging.getLogger("screfinery.resourcehandler")


def _default_validate(data, case):
    pass


class ResourceHandler:
    def __init__(self, store, validate):
        self.validate = validate
        self.store = store

    @property
    def resource_name(self):
        return self.store.table_name

    async def index(self, request):
        await check_user_perm(request, f"{self.resource_name}.index")
        db = request.app["db"]
        offset = request.query.get("offset", 0)
        limit = request.query.get("limit", 10)
        response_body = {
            "total_count": 0,
            "items": []
        }
        query = (
            Query.from_(self.store.table)
                .select(func.Count("*"))
        )
        query_str = str(query)
        log.debug(query_str)
        async with db.execute(query_str) as cursor:
            row = await cursor.fetchone()
            response_body["total_count"] = row[0]

        query = (
            Query.from_(self.store.table)
                .select("*")
                .orderby(self.store.table.created)
                .offset(offset)
                .limit(limit)
        )
        query_str = str(query)
        log.debug(query_str)
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                response_body["items"].append(row)

        return web.json_response(response_body, dumps=json_dumps)

    async def create(self, request):
        await check_user_perm(request, f"{self.resource_name}.create")
        data = await request.json()
        self.validate(data, "create")
        resource = await self.store.create(request.app["db"], data)
        return web.json_response(resource, dumps=json_dumps)

    async def update(self, request):
        await check_user_perm(request, f"{self.resource_name}.update")
        data = await request.json()
        resource_id = request.match_info["resource_id"]
        self.validate(data, "update")
        result = await self.store.update_id(request.app["db"], resource_id, data)
        return web.json_response(result, dumps=json_dumps)

    async def remove(self, request):
        await check_user_perm(request, f"{self.resource_name}.remove", )
        resource_id = request.match_info["resource_id"]
        await self.store.remove_id(request.app["db"], resource_id)
        raise web.HTTPNoContent()

    async def find_id(self, request):
        await check_user_perm(request, f"{self.resource_name}.read")
        resource_id = request.match_info["resource_id"]
        result = await self.store.find_id(request.app["db"], resource_id)
        if result is None:
            raise web.HTTPNotFound()
        return web.json_response(result, dumps=json_dumps)

    @classmethod
    def factory(cls, base_path, model, validate=_default_validate):
        handler = cls(model, validate)
        return [
            web.get(base_path + "/", handler.index),
            web.get(base_path + "/{resource_id}", handler.find_id),
            web.post(base_path + "/", handler.create),
            web.put(base_path + "/{resource_id}", handler.update),
            web.delete(base_path + "/{resource_id}", handler.remove),
        ]


class RelResourceHandler(ResourceHandler):

    @property
    def foreign_key(self):
        return getattr(self.table, self.foreign_key_column)

    async def index_for(self, request):
        await check_user_perm(request, f"{self.resource_name}.index")
        db = request.app["db"]
        rel_id = request.match_info["rel_id"]
        offset = request.query.get("offset", 0)
        limit = request.query.get("limit", 10)
        response_body = {
            "total_count": 0,
            "items": []
        }
        query = (
            Query.from_(self.store.table)
                .select(func.Count("*"))
                .where(self.foreign_key == rel_id)
        )
        query_str = str(query)
        log.debug(query_str)
        async with db.execute(query_str) as cursor:
            row = await cursor.fetchone()
            response_body["total_count"] = row[0]
        query = (
            Query.from_(self.store.table)
                .select("*")
                .orderby(self.store.table.created)
                .where(self.foreign_key == rel_id)
                .offset(offset)
                .limit(limit)
        )
        query_str = str(query)
        log.debug(query_str)
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                response_body["items"].append(row)
        return web.json_response(response_body, dumps=json_dumps)

    async def remove_for(self, request):
        await check_user_perm(request, f"{self.resource_name}.remove", )
        rel_id = request.match_info["rel_id"]
        await self.store.remove_all(request.app["db"], self.foreign_key == rel_id)
        raise web.HTTPNoContent()

    @classmethod
    def factory(cls, base_path, model, validate=_default_validate):
        handler = cls(model, validate)
        return [
            web.get(base_path + "/", handler.index),
            web.get(base_path + "/{rel_id}", handler.index_for),
            web.post(base_path + "/", handler.create),
            web.delete(base_path + "/{rel_id}", handler.remove_for),
        ]