from pypika import Table
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


class DateTime(Function):
    def __init__(self, term, alias=None):
        super().__init__("DATETIME", term, alias=alias)
