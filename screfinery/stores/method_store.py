"""
CRUD methods for `method` objects.
"""

from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, contains_eager

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.stores.model import Method, MethodOre, Ore
from screfinery.util import first, sa_filter_from_dict, sa_order_by_from_dict

resource_name = "method"


def get_by_id(db: Session, method_id: int) -> Method:
    main_query = db.query(Method).filter(Method.id == method_id).subquery()
    return first(
        db.query(Method)
        .join(main_query, main_query.c.id == Method.id)
        .outerjoin(Method.efficiencies)
        .outerjoin(MethodOre.ore)
        .options(
            contains_eager(Method.efficiencies)
            .contains_eager(MethodOre.ore)
        )
        .all()
    )


def list_all(db: Session,
             offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None
             ) -> Tuple[int, List[Method]]:
    filter_ = sa_filter_from_dict(Method, filter_)
    order_by = sa_order_by_from_dict(Method, sort)
    main_query = (
        db.query(Method)
        .filter(filter_)
        .limit(limit)
        .offset(offset)
        .subquery()
    )
    return (
        db.query(Method).filter(filter_).count(),
        (
            db.query(Method)
            .join(main_query, main_query.c.id == Method.id)
            .outerjoin(Method.efficiencies)
            .outerjoin(MethodOre.ore)
            .options(
                contains_eager(Method.efficiencies)
                .contains_eager(MethodOre.ore)
            )
            .order_by(*order_by)
            .all()
        )
    )


def _create_checked_method_ore_rel(db: Session, method: Method, efficiency: schema.MethodOreEfficiency):
    ore = db.query(Ore).filter(Ore.id == efficiency.ore_id).first()
    if ore is None:
        raise IntegrityError(f"Ore with id `{efficiency.ore_id}` does not exist")
    return MethodOre(
        method=method,
        ore=ore,
        efficiency=efficiency.efficiency,
        duration=efficiency.duration,
        cost=efficiency.cost,
    )


def create_one(db: Session, method: schema.MethodCreate) -> Method:
    db_method = Method(
        name=method.name,
    )
    db_method.efficiencies = [
        _create_checked_method_ore_rel(db, db_method, efficiency)
        for efficiency in method.efficiencies
    ]
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method


def update_by_id(db: Session, method_id: int, method: schema.MethodUpdate) -> Optional[Method]:
    db_method = get_by_id(db, method_id)
    if db_method is None:
        return None
    if method.name is not None:
        db_method.name = method.name
    if method.efficiencies is not None:
        db_method.efficiencies = [
            _create_checked_method_ore_rel(db, db_method, efficiency)
            for efficiency in method.efficiencies
        ]
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method


def delete_by_id(db: Session, method_id: int):
    db.query(Method).filter(Method.id == method_id).delete()
    db.commit()
