"""
CRUD methods for `mining_session` objects.
"""
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Tuple, List, Optional

from sqlalchemy.orm import Session, contains_eager, joinedload

from screfinery import schema
from screfinery.errors import IntegrityError
from screfinery.schema import Related
from screfinery.stores.model import MiningSession, \
    MiningSessionEntry, User, Station, Ore, Method
from screfinery.util import sa_filter_from_dict, sa_order_by_from_dict

resource_name = "mining_session"


def get_by_id(db: Session, session_id: int) -> MiningSession:
    join_entries = joinedload(MiningSession.entries)
    result = (
        db.query(MiningSession)
        .filter(MiningSession.id == session_id)
        .options(
            joinedload(MiningSession.creator)
        )
        .options(
            joinedload(MiningSession.users_invited)
        )
        .options(
            join_entries
            , join_entries.joinedload(MiningSessionEntry.user)
            , join_entries.joinedload(MiningSessionEntry.ore)
            , join_entries.joinedload(MiningSessionEntry.method)
            , join_entries.joinedload(MiningSessionEntry.station)
            , join_entries.joinedload(MiningSessionEntry.method_eff)
            , join_entries.joinedload(MiningSessionEntry.station_eff)
        )
        .first()
    )
    return result


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
    db_mining_session.users_invited = db.query(User).filter(
        User.id.in_(rel.id for rel in session.users_invited)
    ).all()
    db.add(db_mining_session)
    db.commit()
    db.refresh(db_mining_session)
    return db_mining_session


def update_by_id(db: Session, session_id: int,
                 session: schema.MiningSessionUpdate) -> Optional[MiningSession]:
    db_mining_session = get_by_id(db, session_id)
    if db_mining_session is None:
        return None
    if session.name is not None:
        db_mining_session.name = session.name
    if session.users_invited is not None:
        db_mining_session.users_invited = db.query(User).filter(
            User.id.in_(rel.id for rel in session.users_invited)
        ).all()
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


def update_entry(db: Session, db_mining_session: MiningSession,
                 db_entry: MiningSessionEntry,
                 entry_update: schema.MiningSessionEntryUpdate) -> MiningSession:
    if entry_update.user is not None:
        db_entry.user = _checked_rel(db, User, entry_update.user.id)
    if entry_update.station is not None:
        db_entry.station = _checked_rel(db, Station, entry_update.station.id)
    if entry_update.ore is not None:
        db_entry.ore = _checked_rel(db, Ore, entry_update.ore.id)
    if entry_update.method is not None:
        db_entry.method = _checked_rel(db, Method, entry_update.method.id)
    if entry_update.quantity is not None:
        db_entry.quantity = entry_update.quantity
    if entry_update.duration is not None:
        db_entry.duration = entry_update.duration
    db.add(db_entry)
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


def _round(value: float) -> float:
    try:
        return float(Decimal(value).quantize(Decimal("1.00"), ROUND_HALF_UP))
    except Exception:
        return round(value, 2)


def calc_payout_summary(mining_session: MiningSession) -> schema.MiningSessionPayoutSummary:
    if len(mining_session.entries) == 0:
        return schema.MiningSessionPayoutSummary(
            total_profit=0,
            average_profit=0,
            payouts=[])

    total_profit = Decimal(sum(entry.profit for entry in mining_session.entries))
    users = [mining_session.creator, *mining_session.users_invited]
    num_users = len(users)
    user_profits = {user: Decimal(0) for user in users}
    for entry in mining_session.entries:
        user_profits[entry.user] += Decimal(entry.profit)

    per_user_avg_profit = total_profit / num_users
    user_over_avg = {
        user: profit - per_user_avg_profit
        for user, profit in user_profits.items()
        if profit > per_user_avg_profit
    }
    user_under_avg = {
        user: per_user_avg_profit - profit
        for user, profit in user_profits.items()
        if profit < per_user_avg_profit
    }
    over_avg_sorted = sorted(user_over_avg.items(), key=lambda x: x[1], reverse=True)
    under_avg_sorted = sorted(user_under_avg.items(), key=lambda x: x[1])
    balance_over_avg = dict(user_over_avg)
    payouts = defaultdict(list)
    for user_over, _ in over_avg_sorted:
        for user_under, _ in under_avg_sorted:
            if user_under_avg[user_under] == 0:
                continue
            balance_over = balance_over_avg[user_over]
            balance_under = user_under_avg[user_under]
            amount = min(balance_under, balance_over)
            balance_over_avg[user_over] -= amount
            user_under_avg[user_under] += amount
            payout = schema.MiningSessionPayoutUser(
                user_id=user_under.id,
                user_name=user_under.name,
                amount=amount.quantize(Decimal("1.00"), ROUND_HALF_UP),
            )
            payouts[user_over].append(payout)
    return schema.MiningSessionPayoutSummary(
        total_profit=total_profit.quantize(Decimal("1.00"), ROUND_HALF_UP),
        average_profit=per_user_avg_profit.quantize(Decimal("1.00"), ROUND_HALF_UP),
        user_profits=sorted([
            schema.MiningSessionPayoutUser(
                user_id=user.id,
                user_name=user.name,
                amount=amount.quantize(Decimal("1.00"), ROUND_HALF_UP))
            for user, amount in user_profits.items()
        ], key=lambda x: x.amount, reverse=True),
        payouts=sorted([
            schema.MiningSessionPayoutItem(
                user=user,
                recipients=sorted(payout, key=lambda x: x.amount, reverse=True)
            )
            for user, payout in payouts.items()
        ], key=lambda x: x.user.name, reverse=True),
    )
