"""
CRUD methods for `station` objects.
"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, joinedload

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.stores.model import Station, StationOre, Ore

resource_name = "station"


def get_by_id(db: Session, station_id: int) -> Station:
    return (
        db.query(Station)
        .filter(Station.id == station_id)
        .options(joinedload(Station.efficiencies))
        .first()
    )


def list_all(db: Session, offset: int, limit: int) -> Tuple[int, List[Station]]:
    return (
        db.query(Station).count(),
        (
            db.query(Station)
            .limit(limit if limit >= 0 else None)
            .offset(offset)
            .options(joinedload(Station.efficiencies))
            .all()
        )
    )


def _update_efficiencies(db: Session, station: Station, efficiencies: List[schema.StationOreEfficiency]):
    db.query(StationOre).filter(StationOre.station_id == station.id).delete()
    for efficiency in efficiencies:
        ore = db.query(Ore).filter(Ore.id == efficiency.ore_id).first()
        if ore is None:
            raise IntegrityError(f"Ore with id `{efficiency.ore_id}` does not exist")
        eff = StationOre(
            station=station,
            ore=ore,
            efficiency_bonus=efficiency.efficiency_bonus,
        )
        db.add(eff)
    db.commit()


def create_one(db: Session, station: schema.StationCreate) -> Station:
    db_obj = Station(
        name=station.name,
    )
    db.add(db_obj)
    _update_efficiencies(db, db_obj, station.efficiencies)
    db.commit()
    return db_obj


def update_by_id(db: Session, station_id: int, station: schema.StationUpdate) -> Optional[Station]:
    db_obj = get_by_id(db, station_id)
    if db_obj is None:
        return None
    if station.name is not None:
        db_obj.name = station.name
    _update_efficiencies(db, db_obj, station.efficiencies)
    db.commit()
    return db_obj


def delete_by_id(db: Session, station_id: int):
    db.query(Station).filter(Station.id == station_id).delete()
    db.commit()
