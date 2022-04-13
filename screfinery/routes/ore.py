"""
HTTP endpoints for `ore_store`.
"""
from fastapi import HTTPException, status

from screfinery import schema
from screfinery.crud_routing import crud_router_factory, \
    EndpointsDef, RouteDef
from screfinery.stores import ore_store
from screfinery.util import is_user_authorized


def authorize(user, scope, item=None):
    """
    Ore resource isn't owned by anyone, so don't check ownership with user
    """
    if not is_user_authorized(user, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


ore_routes = crud_router_factory(
    ore_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Ore],
            authorize=authorize,
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Ore,
            authorize=authorize,
        ),
        create=RouteDef(
            request_model=schema.OreCreate,
            response_model=schema.Ore,
            authorize=authorize,
        ),
        update=RouteDef(
            request_model=schema.OreUpdate,
            response_model=schema.Ore,
            authorize=authorize,
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize,
        )
    )
)
