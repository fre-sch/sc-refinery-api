"""
HTTP endpoints for `method_store`
"""
from fastapi import Depends

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_router_factory import EndpointsDef, \
    crud_router_factory, RouteDef
from screfinery.stores import method_store


method_routes = crud_router_factory(
    method_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Method],
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Method,
        ),
        create=RouteDef(
            request_model=schema.MethodCreate,
            response_model=schema.Method,
        ),
        update=RouteDef(
            request_model=schema.MethodUpdate,
            response_model=schema.Method,
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
        )
    ),
    dependencies=[Depends(verify_user_session)]
)