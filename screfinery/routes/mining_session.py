"""
HTTP endpoints for `mining_session_store`
"""
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.crud_routing import crud_router_factory, \
    EndpointsDef, RouteDef
from screfinery.dependency import use_db, verify_user_session
from screfinery.errors import IntegrityError
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
            response_model=schema.MiningSessionWithUsersEntries,
            authorize=authorize
        ),
        create=RouteDef(
            request_model=schema.MiningSessionCreate,
            response_model=schema.MiningSessionWithUsersEntries,
            authorize=authorize
        ),
        update=RouteDef(
            request_model=schema.MiningSessionUpdate,
            response_model=schema.MiningSessionWithUsersEntries,
            authorize=authorize
        ),
        delete=RouteDef(
            request_model=None,
            response_model=None,
            authorize=authorize
        )
    )
)


@mining_session_routes.post("/{resource_id}/entry",
                            tags=["mining_session"],
                            response_model=schema.MiningSessionWithUsersEntries)
def mining_session_create_entry(
        resource_id: int,
        entry: schema.MiningSessionEntryCreate,
        db: Session = Depends(use_db),
        user_session=Depends(verify_user_session)) -> schema.MiningSessionWithUsersEntries:
    db_mining_session = mining_session_store.get_by_id(db, resource_id)
    if db_mining_session is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"mining_session for id `{resource_id}` not found")
    authorize(user_session.user, "mining_session.update", db_mining_session)

    users_invited = set(it.user.id for it in db_mining_session.users_invited)
    if entry.user.id not in users_invited:
        raise IntegrityError(
            f"User `{entry.user.id}` is not invited to mining session `{resource_id}`")

    db_mining_session = mining_session_store.add_entry(db, db_mining_session, entry)
    return db_mining_session
