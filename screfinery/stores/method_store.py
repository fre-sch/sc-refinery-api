"""
CRUD methods for `method` objects.
"""

from typing import Optional

from sqlalchemy.orm import Session, joinedload, contains_eager

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.stores.model import Method, MethodOre, Ore
from screfinery.util import first

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


def list_all(db: Session, offset: int, limit: int) -> tuple[int, list[Method]]:
    main_query = db.query(Method).limit(limit).offset(offset).subquery()
    return (
        db.query(Method).count(),
        (
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
    )


def _update_efficiencies(db: Session, method: Method, efficiencies: list[schema.MethodOreEfficiency]):
    db.query(MethodOre).filter(MethodOre.method_id == method.id).delete()
    for efficiency in efficiencies:
        ore = db.query(Ore).filter(Ore.id == efficiency.ore_id).first()
        if ore is None:
            raise IntegrityError(f"Ore with id `{efficiency.ore_id}` does not exist")
        eff = MethodOre(
            method=method,
            ore=ore,
            efficiency=efficiency.efficiency,
            duration=efficiency.duration,
        )
        db.add(eff)
    db.commit()


def create_one(db: Session, method: schema.MethodCreate) -> Method:
    db_obj = Method(
        name=method.name,
    )
    db.add(db_obj)
    _update_efficiencies(db, db_obj, method.efficiencies)
    db.commit()
    return db_obj


def update_by_id(db: Session, method_id: int, method: schema.MethodUpdate) -> Optional[Method]:
    db_obj = get_by_id(db, method_id)
    if db_obj is None:
        return None
    db_obj.name = method.name
    _update_efficiencies(db, db_obj, method.efficiencies)
    db.commit()
    return db_obj


def delete_by_id(db: Session, method_id: int):
    db.query(Method).filter(Method.id == method_id).delete()
    db.commit()
