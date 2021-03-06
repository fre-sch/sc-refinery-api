"""
Request and response object schemas with validation
- Classes ending in "Create" are used to validate request objects, which are to be
  added to the database.
- Classes ending in "Update" are used to validate request objects, which are to be
  updated in the database.
- Classes without "Create" or "Update" are used to describe the response objects.
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar, Any, List

from pydantic import BaseModel, validator, confloat, constr, conint
from pydantic.generics import GenericModel


ADMIN_SCOPES = {"*",}
USER_SCOPES = {
    "user.read",
    "user.list",
    "station.read",
    "station.list",
    "ore.read",
    "ore.list",
    "method.read",
    "method.list",
    "mining_session.*",
}
ItemT = TypeVar("ItemT")


class Related(BaseModel):
    """
    Generic model for N:M relations
    """
    id: int
    name: Optional[str]

    class Config:
        orm_mode = True


class ListResponse(GenericModel, Generic[ItemT]):
    total_count: int
    items: List[ItemT]


class Login(BaseModel):
    username: constr(max_length=250)
    password: constr(max_length=250)


class UserScope(BaseModel):
    scope: constr(max_length=50)
    created: Optional[datetime]

    class Config:
        orm_mode = True


class User(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    mail: str
    is_google: bool
    is_active: bool
    is_admin: bool
    created: datetime
    updated: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, user: "screfinery.stores.model.User") -> "User":
        return cls(
            id=user.id,
            name=user.name,
            mail=user.mail,
            is_google=user.is_google,
            is_active=user.is_active,
            is_admin=ADMIN_SCOPES.issubset(set(it.scope for it in user.scopes)),
            created=user.created,
            updated=user.updated,
            last_login=user.last_login
        )


class UserWithFriends(User):
    friends: List[Related]
    sessions_invited: List[Related]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, user: "screfinery.stores.model.User") -> "UserWithFriends":
        return cls(
            id=user.id,
            name=user.name,
            mail=user.mail,
            is_google=user.is_google,
            is_active=user.is_active,
            created=user.created,
            updated=user.updated,
            last_login=user.last_login,
            is_admin=ADMIN_SCOPES.issubset(set(it.scope for it in user.scopes)),
            friends=user.friends,
            sessions_invited=user.sessions_invited
        )


class UserCreate(BaseModel):
    name: constr(max_length=50)
    mail: constr(max_length=250, regex=r"^[^@]+@[^@]+$")
    password: constr(max_length=250)
    password_confirm: constr(max_length=250)
    is_google: bool
    is_active: bool
    is_admin: bool

    @property
    def scopes(self) -> List[str]:
        if self.is_admin:
            return list(ADMIN_SCOPES)
        return list(USER_SCOPES)

    @validator("password_confirm")
    def passwords_match(cls, value, values, **kwargs):
        if 'password' in values and value != values['password']:
            raise ValueError('passwords do not match')
        return value


class UserUpdate(BaseModel):
    name: Optional[constr(max_length=50)]
    mail: Optional[constr(max_length=250, regex=r"^[^@]+@[^@]+$")]
    password: Optional[constr(max_length=250)]
    password_confirm: Optional[constr(max_length=250)]
    is_google: Optional[bool]
    is_active: Optional[bool]
    is_admin: Optional[bool]
    friends: Optional[List[Related]]

    @property
    def scopes(self) -> List[str]:
        if self.is_admin:
            return list(ADMIN_SCOPES)
        return list(USER_SCOPES)

    @validator("password")
    def password_match(cls, value, values, **kwargs):
        if values.get("password_confirm") is None:
            raise ValueError('password_confirm is required')

    @validator("password_confirm")
    def password_confirm_match(cls, value, values, **kwargs):
        if value != values.get("password"):
            raise ValueError('passwords do not match')
        return value


class Ore(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    sell_price: int
    created: datetime
    updated: datetime

    class Config:
        orm_mode = True


class OreCreate(BaseModel):
    name: constr(max_length=50)
    sell_price: int


class OreUpdate(BaseModel):
    name: Optional[constr(max_length=50)]
    sell_price: Optional[int]


class StationOreEfficiency(BaseModel):
    efficiency_bonus: confloat(ge=-1, le=1)
    ore_id: int
    ore_name: Optional[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any):
        return cls(
            efficiency_bonus=obj.efficiency_bonus,
            ore_id=obj.ore_id,
            ore_name=obj.ore.name
        )


class Station(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    created: datetime
    updated: datetime
    efficiencies: List[StationOreEfficiency]

    class Config:
        orm_mode = True


class StationCreate(BaseModel):
    name: constr(max_length=50)
    efficiencies: List[StationOreEfficiency]


class StationUpdate(BaseModel):
    name: Optional[constr(max_length=50)]
    efficiencies: Optional[List[StationOreEfficiency]]


class MethodOreEfficiency(BaseModel):
    efficiency: confloat(ge=0, le=1)
    duration: confloat(ge=0)
    cost: confloat(ge=0)
    ore_id: int
    ore_name: Optional[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any):
        return cls(
            efficiency=obj.efficiency,
            duration=obj.duration,
            cost=obj.cost,
            ore_id=obj.ore_id,
            ore_name=obj.ore.name
        )


class Method(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    created: datetime
    updated: datetime
    efficiencies: List[MethodOreEfficiency]

    class Config:
        orm_mode = True


class MethodCreate(BaseModel):
    name: constr(max_length=50)
    efficiencies: List[MethodOreEfficiency]


class MethodUpdate(BaseModel):
    name: Optional[constr(max_length=50)]
    efficiencies: Optional[List[MethodOreEfficiency]]


class MiningSessionEntry(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    session_id: int
    user: Related
    station: Related
    ore: Related
    method: Related
    created: datetime
    updated: datetime
    quantity: int
    duration: int
    profit: float
    cost: float

    # method_eff: object
    # station_eff: object

    class Config:
        orm_mode = True


class MiningSessionEntryCreate(BaseModel):
    user: Related
    station: Related
    ore: Related
    method: Related
    quantity: conint(gt=0)
    duration: conint(ge=0)


class MiningSessionEntryUpdate(BaseModel):
    user: Optional[Related]
    station: Optional[Related]
    ore: Optional[Related]
    method: Optional[Related]
    quantity: Optional[conint(gt=0)]
    duration: Optional[conint(ge=0)]


class MiningSession(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    creator: Related
    name: str
    created: datetime
    updated: datetime
    archived: Optional[datetime]
    yield_scu: Optional[float]
    yield_uec: Optional[float]

    class Config:
        orm_mode = True


class MiningSessionWithUsersEntries(MiningSession):
    users_invited: List[Related]
    entries: List[MiningSessionEntry]

    class Config:
        orm_mode = True


class MiningSessionListItem(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    creator: Related
    name: str
    created: datetime
    updated: datetime
    archived: Optional[datetime]
    yield_scu: Optional[float]
    yield_uec: Optional[float]
    entries_count: int
    users_invited_count: int

    class Config:
        orm_mode = True


class MiningSessionCreate(BaseModel):
    creator_id: int
    name: constr(max_length=50)
    users_invited: List[Related]


class MiningSessionUpdate(BaseModel):
    name: Optional[constr(max_length=50)]
    archived: Optional[datetime]
    yield_scu: Optional[float]
    yield_uec: Optional[float]
    users_invited: Optional[List[Related]]


class MiningSessionPayoutUser(BaseModel):
    user_id: int
    user_name: str
    amount: float


class MiningSessionPayoutItem(BaseModel):
    user: Related
    recipients: List[MiningSessionPayoutUser]


class MiningSessionPayoutSummary(BaseModel):
    average_profit: float
    total_profit: float
    user_profits: List[MiningSessionPayoutUser]
    payouts: List[MiningSessionPayoutItem]