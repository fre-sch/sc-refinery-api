from pypika import Table, Case
from pypika.functions import Function


User = Table("user")
UserSession = Table("user_session")
UserPerm = Table("user_perm")
Station = Table("station")
Ore = Table("ore")
Method = Table("method")
MethodOre = Table("method_ore")
StationOre = Table("station_ore")
MiningSession = Table("mining_session")
MiningSessionUser = Table("mining_session_user")
MiningSessionEntry = Table("mining_session_entry")


class DateTime(Function):
    def __init__(self, term, alias=None):
        super().__init__("DATETIME", term, alias=alias)


def DateTimeOpt(field, alias):
    return Case().when(field != None, DateTime(field)).else_(None).as_(alias)
