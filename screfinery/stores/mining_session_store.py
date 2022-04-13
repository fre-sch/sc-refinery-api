"""
CRUD methods for `mining_session` objects.
"""
from typing import Tuple, List

from sqlalchemy.orm import Session, contains_eager

from screfinery import schema
from screfinery.stores.model import MiningSession

resource_name = "mining_session"


def get_by_id(db: Session, session_id: int) -> MiningSession:
    main_query = (
        db.query(MiningSession)
        .filter(MiningSession.id == session_id)
        .subquery()
    )
    return main_query.first()


def list_all(db: Session, offset: int, limit: int) -> Tuple[int, List[MiningSession]]:
    return (
        db.query(MiningSession).count(),
        db.query(MiningSession)
        .join(MiningSession.creator)
        .options(contains_eager(MiningSession.creator))
        .limit(limit if limit >= 0 else None)
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
