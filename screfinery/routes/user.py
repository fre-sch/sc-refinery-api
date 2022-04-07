"""
HTTP endpoints for `user_store`
"""
from fastapi import Depends, HTTPException, Request

import screfinery.util
from screfinery import schema
from screfinery.dependency import use_config, use_db, verify_user_session
from screfinery.crud_router_factory import crud_router_factory, \
    RouteDef, EndpointsDef
from screfinery.routes import auth
from screfinery.stores import user_store


def update_user(request: Request, resource_id: int, user: schema.UserUpdate,
                db=Depends(use_db), config=Depends(use_config)) -> schema.User:
    if user.password_confirm:
        user.password = screfinery.util.hash_password(user.password_confirm, config.main.password_salt)
    db_user = user_store.update_by_id(db, resource_id, user)
    if db_user is None:
        raise HTTPException(status_code=404,
                            detail=f"{user_store.resource_name} for id `{resource_id}` not found")
    return db_user


user_routes = crud_router_factory(
    user_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.User]
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.User
        ),
        create=RouteDef(
            request_model=schema.UserCreate,
            response_model=schema.User
        ),
        update=RouteDef(
            request_model=None,
            response_model=None,
            custom_handler_func=update_user
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None
        )
    ),
    dependencies=[Depends(verify_user_session)]
)
