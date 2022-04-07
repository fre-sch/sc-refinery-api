"""
HTTP endpoints for `ore_store`.
"""
from fastapi import Depends

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_router_factory import crud_router_factory, \
    EndpointsDef, RouteDef
from screfinery.stores import ore_store


ore_routes = crud_router_factory(
    ore_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Ore]
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Ore
        ),
        create=RouteDef(
            request_model=schema.OreCreate,
            response_model=schema.Ore
        ),
        update=RouteDef(
            request_model=schema.OreUpdate,
            response_model=schema.Ore
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None
        )
    ),
    dependencies=[Depends(verify_user_session)]
)
