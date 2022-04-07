"""
CRUD methods for `mining_session` objects.
"""

from sqlalchemy.orm import Session, joinedload, contains_eager, aliased

from screfinery import schema
from screfinery.stores.model import MiningSession, MiningSessionUser, User
from screfinery.util import first

resource_name = "mining_session"


def get_by_id(db: Session, session_id: int) -> MiningSession:
    main_query = db.query(MiningSession).filter(MiningSession.id == session_id).subquery()
    return first(
        db.query(MiningSession)
        .all()
    )


def list_all(db: Session, offset: int, limit: int) -> tuple[int, list[MiningSession]]:
    return (
        db.query(MiningSession).count(),
        db.query(MiningSession)
        .join(MiningSession.creator)
        .options(
            contains_eager(MiningSession.creator)
        )
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
