"""
HTTP endpoints for `mining_session_store`
"""
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.crud_routing import crud_router_factory, \
    EndpointsDef, RouteDef, CRUD_SCOPE_CREATE, CRUD_SCOPE_UPDATE, CRUD_SCOPE_DELETE
from screfinery.dependency import use_db, verify_user_session
from screfinery.errors import IntegrityError, NotFoundError
from screfinery.stores import mining_session_store
from screfinery.util import is_user_authorized, first


def authorize(user, scope, item=None):
    if item is not None:
        try:
            if item.user_id == user.id:
                return
        except AttributeError:
            pass
        try:
            if item.creator_id == user.id:
                return
        except AttributeError:
            pass
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
        raise NotFoundError("mining_session", resource_id)
    authorize(user_session.user, f"mining_session.{CRUD_SCOPE_CREATE}", db_mining_session)

    users_invited = set(it.user.id for it in db_mining_session.users_invited)
    if entry.user.id not in users_invited:
        raise IntegrityError(
            f"User `{entry.user.id}` is not invited to mining session `{resource_id}`")

    db_mining_session = mining_session_store.add_entry(db, db_mining_session, entry)
    return db_mining_session


@mining_session_routes.put("/{resource_id}/entry/{entry_id}",
                           tags=["mining_session"],
                           response_model=schema.MiningSessionWithUsersEntries)
def mining_session_update_entry(
        resource_id: int,
        entry_id: int,
        entry: schema.MiningSessionEntryUpdate,
        db: Session = Depends(use_db),
        user_session=Depends(verify_user_session)) -> schema.MiningSessionWithUsersEntries:
    db_mining_session = mining_session_store.get_by_id(db, resource_id)
    if db_mining_session is None:
        raise NotFoundError("mining_session", resource_id)
    authorize(user_session.user, f"mining_session.{CRUD_SCOPE_UPDATE}", db_mining_session)
    db_entry = first(
        entry for entry in db_mining_session.entries
        if entry.id == entry_id
    )
    if db_entry is None:
        raise NotFoundError("mining_session.entry", entry_id)
    authorize(user_session.user, f"mining_session.{CRUD_SCOPE_UPDATE}", db_entry)
    db_mining_session = mining_session_store.update_entry(
        db, db_mining_session, db_entry, entry)
    return db_mining_session



@mining_session_routes.delete("/{resource_id}/entry/{entry_id}",
                              tags=["mining_session"],
                              response_model=schema.MiningSessionWithUsersEntries)
def mining_session_delete_entry(
        resource_id: int, entry_id: int,
        db: Session = Depends(use_db), user_session = Depends(verify_user_session)
        ) -> schema.MiningSessionWithUsersEntries:
    db_mining_session = mining_session_store.get_by_id(db, resource_id)
    if db_mining_session is None:
        raise NotFoundError("mining_session", resource_id)
    db_entry = first(
        entry for entry in db_mining_session.entries
        if entry.id == entry_id
    )
    if db_entry is None:
        raise NotFoundError("mining_session.entry", entry_id)
    authorize(user_session.user, f"mining_session.{CRUD_SCOPE_DELETE}", db_entry)
    db_mining_session = mining_session_store.delete_entry(
        db, db_mining_session, db_entry)
    return db_mining_session