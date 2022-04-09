"""
HTTP endpoints for `method_store`
"""
from fastapi import Depends, HTTPException, status

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_routing import EndpointsDef, \
    crud_router_factory, RouteDef
from screfinery.stores import method_store
from screfinery.util import is_user_authorized


def authorize(user, scope, item=None):
    """
    Method resource isn't owned by anyone, so don't check ownership with user
    """
    if not is_user_authorized(user, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


method_routes = crud_router_factory(
    method_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Method],
            authorize=authorize,
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Method,
            authorize=authorize,
        ),
        create=RouteDef(
            request_model=schema.MethodCreate,
            response_model=schema.Method,
            authorize=authorize,
        ),
        update=RouteDef(
            request_model=schema.MethodUpdate,
            response_model=schema.Method,
            authorize=authorize,
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize,
        )
    )
)