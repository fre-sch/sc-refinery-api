"""
HTTP endpoints for `mining_session_store`
"""
from fastapi import Depends, HTTPException, status

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_routing import crud_router_factory, \
    EndpointsDef, RouteDef
from screfinery.stores import mining_session_store
from screfinery.util import is_user_authorized


def authorize(user, scope, item=None):
    if item is not None and item.creator_id == user.id:
        return True

    if not is_user_authorized(user, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


mining_session_routes = crud_router_factory(
    mining_session_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.MiningSessionListItem],
            authorize=authorize
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.MiningSession,
            authorize=authorize
        ),
        create=RouteDef(
            request_model=schema.MiningSessionCreate,
            response_model=schema.MiningSession,
            authorize=authorize
        ),
        update=RouteDef(
            request_model=schema.MiningSessionUpdate,
            response_model=schema.MiningSession,
            authorize=authorize
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize
        )
    )
)