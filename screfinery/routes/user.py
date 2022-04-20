"""
HTTP endpoints for `user_store`
"""
from typing import List

from fastapi import Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.crud_routing import crud_router_factory, \
    RouteDef, EndpointsDef
from screfinery.dependency import use_config, use_db, verify_user_session
from screfinery.errors import NotFoundError
from screfinery.schema import Friendship
from screfinery.stores import user_store
from screfinery.util import hash_password, is_user_authorized, obj


def authorize(user, scope, item=None):
    if item is not None and user.id == item.id:
        return True

    if not is_user_authorized(user, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


def create_user(item: schema.UserCreate, db: Session = Depends(use_db),
                config=Depends(use_config)):
    return user_store.create_one(db, item, config.app.password_salt)


def update_user(resource_id: int, user: schema.UserUpdate,
                db=Depends(use_db), config=Depends(use_config),
                user_session=Depends(verify_user_session)) -> schema.User:
    authorize(user_session.user, "user.update", obj(id=resource_id))
    if user.password_confirm:
        user.password = hash_password(config.app.password_salt,
                                      user.password_confirm)
    db_user = user_store.update_by_id(db, resource_id, user)
    if db_user is None:
        raise NotFoundError("user", resource_id)
    return db_user


user_routes = crud_router_factory(
    user_store,
    EndpointsDef(
        list=RouteDef(
            request_model=None,
            response_model=schema.ListResponse[schema.User],
            authorize=authorize,
        ),
        read=RouteDef(
            request_model=None,
            response_model=schema.UserWithFriends,
            authorize=authorize,
        ),
        create=RouteDef(
            request_model=schema.UserCreate,
            response_model=schema.UserWithFriends,
            custom_handler_func=create_user,
        ),
        update=RouteDef(
            request_model=schema.UserUpdate,
            response_model=schema.UserWithFriends,
            custom_handler_func=update_user
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize,
        )
    )
)


@user_routes.get("/{user_id}/friendship",
                 response_model=schema.FriendshipList, tags=["user"])
def list_friendship(user_id: int, db: Session = Depends(use_db),
                    user_session=Depends(verify_user_session)) -> schema.FriendshipList:
    db_user = user_store.get_friendship(db, user_id)
    if db_user is None:
        raise NotFoundError("user", user_id)
    authorize(user_session.user, "user.read", db_user)
    return schema.FriendshipList(
        friends_outgoing=db_user.friends_outgoing,
        friends_incoming=db_user.friends_incoming,
    )


@user_routes.put("/{user_id}/friendship",
                 response_model=schema.FriendshipList, tags=["user"])
def update_friendship(user_id: int,
                      friendship_list: schema.FriendshipListUpdate,
                      db: Session = Depends(use_db),
                      user_session=Depends(verify_user_session)) -> schema.FriendshipList:
    db_user = user_store.get_friendship(db, user_id)
    if db_user is None:
        raise NotFoundError("user", user_id)
    authorize(user_session.user, "user.update", db_user)
    user_store.update_friendship(db, db_user, friendship_list)
    return db_user
