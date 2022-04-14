"""
CRUD methods for `mining_session` objects.
"""
from typing import Tuple, List

from sqlalchemy.orm import Session, contains_eager

from screfinery import schema
from screfinery.stores.model import MiningSession
from screfinery.util import sa_filter_from_dict, sa_order_by_from_dict

resource_name = "mining_session"


def get_by_id(db: Session, session_id: int) -> MiningSession:
    main_query = (
        db.query(MiningSession)
        .filter(MiningSession.id == session_id)
        .subquery()
    )
    return main_query.first()


def list_all(db: Session, offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None,
             ) -> Tuple[int, List[MiningSession]]:
    filter_ = sa_filter_from_dict(MiningSession, filter_)
    order_by = sa_order_by_from_dict(MiningSession, sort)
    return (
        db.query(MiningSession).filter(filter_).count(),
        db.query(MiningSession)
        .join(MiningSession.creator)
        .options(contains_eager(MiningSession.creator))
        .filter(filter_)
        .order_by(*order_by)
        .limit(limit)
        .offset(offset)
        .all()
    )


def create_one(db: Session, session: schema.MiningSessionCreate) -> MiningSession:
    db_session = MiningSession(
        name=session.name,
        creator_id=session.creator_id
    )
    db.add(db_session)
    db.commit()
    return db_session
