from dataclasses import dataclass
from typing import Optional, Callable, Type

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from screfinery.dependency import use_db, verify_scopes
from screfinery.types import Store


@dataclass
class RouteDef:
    request_model: Optional[Type]
    response_model: Optional[Type]
    custom_handler_func: Optional[Callable] = None


@dataclass
class EndpointsDef:
    list: Optional[RouteDef] = None
    read: Optional[RouteDef] = None
    create: Optional[RouteDef] = None
    update: Optional[RouteDef] = None
    delete: Optional[RouteDef] = None


def crud_router_factory(store: Store, endpoints: EndpointsDef,
                        route_prefix: str = None, dependencies=None):
    """
    Creates basic list, read, create, update, delete HTTP endpoints and routes for
    a resource store

    Example:
        >>> from screfinery.crud_router_factory import crud_router_factory
        >>> router = crud_router_factory(
        ...     user_store
        ...     EndpointsDef(
        ...         list=RouteDef(
        ...             request_model=None,
        ...             response_model=schema.ListResponse[schema.User]
        ...         ),
        ...         read=RouteDef(None, schema.User),
        ...         create=RouteDef(schema.UserCreate, schema.User, custom_create_user),
        ...         update=RouteDef(schema.UserUpdate, schema.User),
        ...         delete=RouteDef(None, None),
        ...     )
        ... )

    """
    route_prefix = route_prefix if route_prefix is not None else f"/{store.resource_name}"
    routes = APIRouter(prefix=route_prefix, dependencies=dependencies)
    setup_route_list(routes, endpoints.list, store)
    setup_route_read(routes, endpoints.read, store)
    setup_route_create(routes, endpoints.create, store)
    setup_route_update(routes, endpoints.update, store)
    setup_route_delete(routes, endpoints.delete, store)
    return routes


def setup_route_list(routes: APIRouter, route_def: RouteDef, store: Store):
    if route_def is None:
        return

    tags = [store.resource_name]

    if route_def.custom_handler_func is not None:
        routes.add_api_route(
            "/", route_def.custom_handler_func, methods=["GET"],
            response_model=route_def.response_model, tags=tags
        )
        return

    response_model = route_def.response_model
    require_scope = verify_scopes(f"{store.resource_name}.list")

    @routes.get("/", response_model=response_model, tags=tags)
    def list_resource(offset: int = 0, limit: int = 10,
                      db: Session = Depends(use_db),
                      is_authorized: bool = Depends(require_scope)):
        total_count, items = store.list_all(db, offset, limit)
        return response_model(total_count=total_count, items=items)


def setup_route_read(routes: APIRouter, route_def: RouteDef, store: Store):
    if route_def is None:
        return

    tags = [store.resource_name]

    if route_def.custom_handler_func is not None:
        routes.add_api_route(
            "/{resource_id}", route_def.custom_handler_func, methods=["GET"],
            response_model=route_def.response_model, tags=tags)
        return

    require_scope = verify_scopes(f"{store.resource_name}.read")

    @routes.get("/{resource_id}",
                response_model=route_def.response_model, tags=tags)
    def read_resource(resource_id: int, db: Session = Depends(use_db),
                      is_authorized: bool = Depends(require_scope)):
        item = store.get_by_id(db, resource_id)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail=f"{store.resource_name} for id `{resource_id}` not found")
        return item


def setup_route_create(routes: APIRouter, route_def: RouteDef, store: Store):
    if route_def is None:
        return

    tags = [store.resource_name]

    if route_def.custom_handler_func is not None:
        routes.add_api_route(
            "/", route_def.custom_handler_func, methods=["POST"],
            response_model=route_def.response_model, tags=tags)
        return

    require_scope = verify_scopes(f"{store.resource_name}.create")

    @routes.post("/", response_model=route_def.response_model, tags=tags)
    def create_resource(item: route_def.request_model,
                        db: Session = Depends(use_db),
                        is_authorized: bool = Depends(require_scope)):
        return store.create_one(db, item)


def setup_route_update(routes: APIRouter, route_def: RouteDef, store: Store):
    if route_def is None:
        return

    tags = [store.resource_name]

    if route_def.custom_handler_func is not None:
        routes.add_api_route(
            "/{resource_id}", route_def.custom_handler_func, methods=["PUT"],
            response_model=route_def.response_model, tags=tags)
        return

    require_scope = verify_scopes(f"{store.resource_name}.update")

    @routes.put("/{resource_id}",
                response_model=route_def.response_model, tags=tags)
    def update_resource(resource_id: int,
                        item: route_def.request_model,
                        db: Session = Depends(use_db),
                        is_authorized: bool = Depends(require_scope)):
        item = store.update_by_id(db, resource_id, item)
        if item is None:
            raise HTTPException(
                HTTP_404_NOT_FOUND,
                detail=f"{store.resource_name} for id `{resource_id}` not found")
        return item


def setup_route_delete(routes: APIRouter, route_def: RouteDef, store: Store):
    if route_def is None:
        return

    tags = [store.resource_name]

    if route_def.custom_handler_func is not None:
        routes.add_api_route(
            "/{resource_id}", route_def.custom_handler_func, methods=["DELETE"],
            response_model=route_def.response_model, tags=tags)
        return

    require_scope = verify_scopes(f"{store.resource_name}.delete")

    @routes.delete("/{resource_id}",
                   response_model=route_def.response_model, tags=tags)
    def delete_resource(resource_id: int, db: Session = Depends(use_db),
                        is_authorized: bool = Depends(require_scope)):
        store.delete_by_id(db, resource_id)
        return Response(status_code=204)
