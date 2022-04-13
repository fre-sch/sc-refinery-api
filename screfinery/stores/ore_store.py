"""
CRUD methods for `ore` objects.
"""

from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.stores.model import Ore

resource_name = "ore"


def get_by_id(db: Session, ore_id: int) -> Ore:
    return db.query(Ore).filter(Ore.id == ore_id).first()


def list_all(db: Session, offset: int, limit: int) -> Tuple[int, List[Ore]]:
    return (
        db.query(Ore).count(),
        db.query(Ore)
        .offset(offset)
        .limit(limit if limit >= 0 else None)
        .all()
    )


def create_one(db: Session, ore: schema.OreCreate) -> Optional[Ore]:
    db_obj = Ore(name=ore.name)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_by_id(db: Session, ore_id: int, ore: schema.OreUpdate) -> Optional[Ore]:
    db_obj = get_by_id(db, ore_id)
    if not db_obj:
        return
    db_obj.name = ore.name
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_by_id(db: Session, ore_id: int):
    db.query(Ore).filter(Ore.id == ore_id).delete()
    db.commit()
