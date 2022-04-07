"""
HTTP endpoints for `station_store`
"""
from fastapi import Depends

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_router_factory import EndpointsDef, RouteDef, \
    crud_router_factory
from screfinery.stores import station_store


station_routes = crud_router_factory(
    station_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.Station]
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.Station
        ),
        create=RouteDef(
            request_model=schema.StationCreate,
            response_model=schema.Station
        ),
        update=RouteDef(
            request_model=schema.StationUpdate,
            response_model=schema.Station
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None
        )
    ),
    dependencies=[Depends(verify_user_session)]
)
