"""
HTTP endpoints for `mining_session_store`
"""
from fastapi import Depends

from screfinery import schema
from screfinery.dependency import verify_user_session
from screfinery.crud_router_factory import crud_router_factory, \
    EndpointsDef, RouteDef
from screfinery.stores import mining_session_store


mining_session_routes = crud_router_factory(
    mining_session_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.MiningSessionListItem],
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.MiningSession,
        ),
        create=RouteDef(
            request_model=schema.MiningSessionCreate,
            response_model=schema.MiningSession,
        ),
        update=RouteDef(
            request_model=schema.MiningSessionUpdate,
            response_model=schema.MiningSession,
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None
        )
    ),
    dependencies=[Depends(verify_user_session)]
)