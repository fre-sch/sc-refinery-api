import logging

from pypika import Query
from pypika import functions as fn

from screfinery.basestore import BaseStore, group_init, group_rows, group_rel_many, \
    group_rel_one
from screfinery.storage.table import MiningSession, DateTime, DateTimeOpt, \
    MiningSessionUser, \
    MiningSessionEntry

log = logging.getLogger("screfinery.storage")


index_groups = group_rows(
    group_init(lambda row: row["id"],
               "id", "name", "created", "updated", "archived", "is_archived",
               "yield_scu", "yield_uec"),
    group_rel_one("creator", "creator_id", "creator_name"),
    group_rel_many("users", "user_id", "user_name")
)

item_groups = group_rows(
    group_init(lambda row: row["id"],
               "id", "name", "created", "updated", "archived", "is_archived",
               "yield_scu", "yield_uec"),
    group_rel_one("creator", "creator_id", "creator_name"),
    group_rel_many("users", "user_id", "user_name")
)


class MiningSessionStore(BaseStore):

    def __init__(self):
        super().__init__(MiningSession)

    def find_one_query(self, criteria):
        return (
            Query.from_(MiningSession)
            .select(
                MiningSession.id,
                MiningSession.creator_id,
                MiningSession.name,
                DateTime(MiningSession.created).as_("created"),
                DateTime(MiningSession.updated).as_("updated"),
                DateTimeOpt(MiningSession.archived, "archived"),
                MiningSession.archived.notnull().as_("is_archived"),
                MiningSession.yield_scu,
                MiningSession.yield_uec,
                Query.from_(MiningSessionUser)
                .select(fn.Count(MiningSessionUser.user_id))
                .where(MiningSessionUser.mining_session_id==MiningSession.id)
                .as_("count_users"),
                Query.from_(MiningSessionEntry)
                .select(fn.Count(MiningSessionEntry.id))
                .where(MiningSessionEntry.mining_session_id == MiningSession.id)
                .as_("count_entries")
            )
            .where(criteria)
            .limit(1)
        )

    async def find_all(self, db, criteria=None, sort=None, offset=0, limit=10):
        total_count = await self.count_by(db, criteria)
        query = (
            Query.from_(MiningSession)
            .select(
                MiningSession.id,
                MiningSession.creator_id,
                MiningSession.name,
                DateTime(MiningSession.created).as_("created"),
                DateTime(MiningSession.updated).as_("updated"),
                DateTimeOpt(MiningSession.archived, "archived"),
                MiningSession.archived.notnull().as_("is_archived"),
                MiningSession.yield_scu,
                MiningSession.yield_uec,
                Query.from_(MiningSessionUser)
                .select(fn.Count(MiningSessionUser.user_id))
                .where(MiningSessionUser.mining_session_id==MiningSession.id)
                .as_("count_users"),
                Query.from_(MiningSessionEntry)
                .select(fn.Count(MiningSessionEntry.id))
                .where(MiningSessionEntry.mining_session_id == MiningSession.id)
                .as_("count_entries")
            )
            .where(criteria)
        )
        query = self.apply_sort(query, sort)
        query_str = str(query)
        log.debug(f"MiningSessionStore.find_all {query_str}")
        items = []
        async with db.execute(query_str) as cursor:
            async for row in cursor:
                items.append(row)
        return total_count, items


def mining_session_validate(data, case):
    pass