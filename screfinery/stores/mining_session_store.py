"""
CRUD methods for `mining_session` objects.
"""
from typing import Tuple, List, Optional

from sqlalchemy.orm import Session, contains_eager, joinedload

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.stores.model import MiningSession, MiningSessionUser, \
    MiningSessionEntry, User, Station, Ore, Method
from screfinery.util import sa_filter_from_dict, sa_order_by_from_dict

resource_name = "mining_session"


def get_by_id(db: Session, session_id: int) -> MiningSession:
    return (
        db.query(MiningSession)
        .filter(MiningSession.id == session_id)
        .options(
            joinedload(MiningSession.creator)
        )
        .options(
            joinedload(MiningSession.users_invited)
            .joinedload(MiningSessionUser.user)
        )
        .options(
            joinedload(MiningSession.entries).joinedload(MiningSessionEntry.station)
            , joinedload(MiningSession.entries).joinedload(MiningSessionEntry.ore)
            , joinedload(MiningSession.entries).joinedload(MiningSessionEntry.method)
            , joinedload(MiningSession.entries).joinedload(MiningSessionEntry.method_eff)
            , joinedload(MiningSession.entries).joinedload(MiningSessionEntry.station_eff)
        )
        .first()
    )


def list_all(db: Session, offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None,
             ) -> Tuple[int, List[MiningSession]]:
    filter_ = sa_filter_from_dict(MiningSession, filter_)
    order_by = sa_order_by_from_dict(MiningSession, sort)
    return (
        db.query(MiningSession).filter(filter_).count(),
        db.query(MiningSession)
        .options(joinedload(MiningSession.creator))
        .filter(filter_)
        .order_by(*order_by)
        .limit(limit)
        .offset(offset)
        .all()
    )


def create_one(db: Session, session: schema.MiningSessionCreate) -> MiningSession:
    creator = db.query(User).filter(User.id == session.creator_id).first()
    if not creator:
        raise IntegrityError(f"user for id `{session.creator_id}` not found")
    db_mining_session = MiningSession(
        name=session.name,
        creator=creator,
    )
    db_mining_session.users_invited = [
        _create_checked_mining_session_user_rel(db, db_mining_session, rel)
        for rel in session.users_invited
    ]
    db.add(db_mining_session)
    db.commit()
    db.refresh(db_mining_session)
    return db_mining_session


def _create_checked_mining_session_user_rel(
        db: Session, mining_session: MiningSession, user_rel: schema.Related
        ) -> MiningSessionUser:
    user_invited = db.query(User).filter(User.id == user_rel.id).first()
    if not user_invited:
        raise IntegrityError(f"user for id `{user_rel.id}` not found")
    return MiningSessionUser(session=mining_session, user=user_invited)


def update_by_id(db: Session, session_id: int,
                 session: schema.MiningSessionUpdate) -> Optional[MiningSession]:
    db_mining_session = get_by_id(db, session_id)
    if db_mining_session is None:
        return None
    if session.name is not None:
        db_mining_session.name = session.name
    if session.users_invited is not None:
        db_mining_session.users_invited = [
            _create_checked_mining_session_user_rel(db, db_mining_session, rel)
            for rel in session.users_invited
        ]
    db.add(db_mining_session)
    db.commit()
    db.refresh(db_mining_session)
    return db_mining_session


def delete_by_id(db: Session, mining_session_id: int):
    db.query(MiningSession).filter(MiningSession.id == mining_session_id).delete()
    db.commit()


def add_entry(db: Session, db_mining_session: MiningSession,
              entry: schema.MiningSessionEntryCreate) -> MiningSession:
    db_entry = MiningSessionEntry(
        session=db_mining_session,
        user=_checked_rel(db, User, entry.user.id),
        station=_checked_rel(db, Station, entry.station.id),
        ore=_checked_rel(db, Ore, entry.ore.id),
        method=_checked_rel(db, Method, entry.method.id),
        quantity=entry.quantity,
        duration=entry.duration,
    )
    db_mining_session.entries.append(db_entry)
    db.add(db_mining_session)
    db.commit()
    db.refresh(db_mining_session)
    return db_mining_session


def delete_entry(db: Session, db_mining_session, db_entry: MiningSessionEntry) -> MiningSession:
    db.delete(db_entry)
    db.commit()
    db.refresh(db_mining_session)
    return db_mining_session


def _checked_rel(db: Session, model, rel_id: int):
    obj = db.query(model).filter(model.id == rel_id).first()
    if not obj:
        raise IntegrityError(f"{model.__name__} for id `{rel_id}` not found")
    return obj
