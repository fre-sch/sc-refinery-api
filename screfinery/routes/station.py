"""
HTTP endpoints for `station_store`
"""
from fastapi import HTTPException, status

from screfinery import schema
from screfinery.crud_routing import EndpointsDef, RouteDef, \
    crud_router_factory
from screfinery.stores import station_store
from screfinery.util import is_user_authorized


def authorize(user, scope, item=None):
    """
    Station resource isn't owned by anyone, so don't check ownership with user
    """
    if not is_user_authorized(user, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


station_routes = crud_router_factory(
    station_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Station],
            authorize=authorize,
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Station,
            authorize=authorize,
        ),
        create=RouteDef(
            request_model=schema.StationCreate,
            response_model=schema.Station,
            authorize=authorize,
        ),
        update=RouteDef(
            request_model=schema.StationUpdate,
            response_model=schema.Station,
            authorize=authorize,
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize,
        )
    )
)
