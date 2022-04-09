from dataclasses import dataclass
from typing import Optional, Callable, Type

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from screfinery.dependency import use_db, verify_user_session
from screfinery.types import Store


@dataclass
class RouteDef:
    request_model: Optional[Type]
    response_model: Optional[Type]
    custom_handler_func: Optional[Callable] = None
    authorize: Optional[Callable] = None


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
        >>> from screfinery.crud_routing import crud_router_factory
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

    @routes.get("/", response_model=response_model, tags=tags)
    def list_resource(offset: int = 0, limit: int = 10,
                      db: Session = Depends(use_db),
                      user_session=Depends(verify_user_session)):
        if route_def.authorize is not None:
            route_def.authorize(user_session.user,
                                f"{store.resource_name}.list")
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

    @routes.get("/{resource_id}",
                response_model=route_def.response_model, tags=tags)
    def read_resource(resource_id: int, db: Session = Depends(use_db),
                      user_session=Depends(verify_user_session)):
        item = store.get_by_id(db, resource_id)
        if route_def.authorize is not None:
            route_def.authorize(user_session.user,
                                f"{store.resource_name}.read", item)
        if item is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
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

    @routes.post("/", response_model=route_def.response_model, tags=tags)
    def create_resource(item: route_def.request_model,
                        db: Session = Depends(use_db),
                        user_session=Depends(verify_user_session)):
        if route_def.authorize is not None:
            route_def.authorize(user_session.user,
                                f"{store.resource_name}.create")
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

    @routes.put("/{resource_id}",
                response_model=route_def.response_model, tags=tags)
    def update_resource(resource_id: int,
                        item: route_def.request_model,
                        db: Session = Depends(use_db),
                        user_session=Depends(verify_user_session)):
        db_item = store.get_by_id(db, resource_id)
        if db_item is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"{store.resource_name} for id `{resource_id}` not found")
        if route_def.authorize is not None:
            route_def.authorize(user_session.user,
                                f"{store.resource_name}.update", db_item)
        item = store.update_by_id(db, resource_id, item)
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

    @routes.delete("/{resource_id}",
                   response_model=route_def.response_model, tags=tags)
    def delete_resource(resource_id: int, db: Session = Depends(use_db),
                        user_session=Depends(verify_user_session)):
        db_item = store.get_by_id(db, resource_id)
        if db_item is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"{store.resource_name} for id `{resource_id}` not found")
        if route_def.authorize is not None:
            route_def.authorize(user_session.user,
                                f"{store.resource_name}.delete", db_item)
        store.delete_by_id(db, resource_id)
        return Response(status_code=204)
