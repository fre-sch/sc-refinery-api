"""
CRUD methods for `ore` objects.
"""

from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from screfinery import schema
from screfinery.stores.model import Ore
from screfinery.util import sa_filter_from_dict, sa_order_by_from_dict

resource_name = "ore"


def get_by_id(db: Session, ore_id: int) -> Ore:
    return db.query(Ore).filter(Ore.id == ore_id).first()


def list_all(db: Session,
             offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None) -> Tuple[int, List[Ore]]:
    filter_ = sa_filter_from_dict(Ore, filter_)
    order_by = sa_order_by_from_dict(Ore, sort)
    return (
        db.query(Ore).filter(filter_).count(),
        db.query(Ore)
        .filter(filter_)
        .order_by(*order_by)
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_one(db: Session, ore: schema.OreCreate) -> Optional[Ore]:
    db_obj = Ore(
        name=ore.name,
        sell_price=ore.sell_price
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_by_id(db: Session, ore_id: int, ore: schema.OreUpdate) -> Optional[Ore]:
    db_obj = get_by_id(db, ore_id)
    if not db_obj:
        return
    if db_obj.name is not None:
        db_obj.name = ore.name
    if db_obj.sell_price is not None:
        db_obj.sell_price = ore.sell_price
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_by_id(db: Session, ore_id: int):
    db.query(Ore).filter(Ore.id == ore_id).delete()
    db.commit()
