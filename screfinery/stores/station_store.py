"""
CRUD methods for `station` objects.
"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, joinedload

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.stores.model import Station, StationOre, Ore
from screfinery.util import sa_filter_from_dict, sa_order_by_from_dict

resource_name = "station"


def get_by_id(db: Session, station_id: int) -> Station:
    return (
        db.query(Station)
        .filter(Station.id == station_id)
        .options(joinedload(Station.efficiencies))
        .first()
    )


def list_all(db: Session,
             offset: int = 0, limit: int = None,
             filter_: dict = None, sort: dict = None
             ) -> Tuple[int, List[Station]]:
    filter_ = sa_filter_from_dict(Station, filter_)
    order_by = sa_order_by_from_dict(Station, sort)
    return (
        db.query(Station).filter(filter_).count(),
        (
            db.query(Station)
            .filter(filter_)
            .order_by(*order_by)
            .limit(limit)
            .offset(offset)
            .options(joinedload(Station.efficiencies))
            .all()
        )
    )


def _create_checked_station_ore_rel(db: Session, station: Station, efficiency: schema.StationOreEfficiency):
    ore = db.query(Ore).filter(Ore.id == efficiency.ore_id).first()
    if ore is None:
        raise IntegrityError(
            f"Ore with id `{efficiency.ore_id}` does not exist")
    return StationOre(
        station=station,
        ore=ore,
        efficiency_bonus=efficiency.efficiency_bonus,
    )


def create_one(db: Session, station: schema.StationCreate) -> Station:
    db_station = Station(
        name=station.name
    )
    db_station.efficiencies = [
        _create_checked_station_ore_rel(db, db_station, eff)
        for eff in station.efficiencies
    ]
    db.add(db_station)
    db.commit()
    return db_station


def update_by_id(db: Session, station_id: int, station: schema.StationUpdate) -> Optional[Station]:
    db_station = get_by_id(db, station_id)
    if db_station is None:
        return None
    if station.name is not None:
        db_station.name = station.name
    if station.efficiencies is not None:
        db_station.efficiencies = [
            _create_checked_station_ore_rel(db, db_station, eff)
            for eff in station.efficiencies
        ]
    db.commit()
    return db_station


def delete_by_id(db: Session, station_id: int):
    db.query(Station).filter(Station.id == station_id).delete()
    db.commit()
