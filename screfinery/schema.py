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

from screfinery.util import optint

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


class Friendship(BaseModel):
    user_id: int
    user_name: str
    friend_id: int
    friend_name: str
    created: datetime
    confirmed: Optional[datetime]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, friendship: "screfinery.stores.model.Friendship") -> "Friendship":
        return cls(
            user_id=friendship.user_id,
            user_name=friendship.user.name,
            friend_id=friendship.friend_id,
            friend_name=friendship.friend.name,
            created=friendship.created,
            confirmed=friendship.confirmed
        )


class FriendshipList(BaseModel):
    friends_outgoing: List[Friendship]
    friends_incoming: List[Friendship]

    class Config:
        orm_mode = True


class FriendshipUpdate(BaseModel):
    user_id: int
    user_name: Optional[constr(max_length=50)]
    friend_id: int
    friend_name: Optional[constr(max_length=50)]
    confirmed: Optional[datetime]
    name: Optional[constr(max_length=50)]


class FriendshipListUpdate(BaseModel):
    friends_outgoing: Optional[List[FriendshipUpdate]]
    friends_incoming: Optional[List[FriendshipUpdate]]


class User(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    mail: str
    is_google: bool
    is_active: bool
    created: datetime
    updated: datetime
    last_login: Optional[datetime]
    scopes: List[str]

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
            created=user.created,
            updated=user.updated,
            last_login=user.last_login,
            scopes=[s.scope for s in user.scopes]
        )


class UserWithFriends(User):
    friends_outgoing: List[Friendship]
    friends_incoming: List[Friendship]

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
            scopes=[s.scope for s in user.scopes],
            friends_outgoing=user.friends_outgoing,
            friends_incoming=user.friends_incoming
        )


class UserCreate(BaseModel):
    name: constr(max_length=50)
    mail: constr(max_length=250, regex=r"^[^@]+@[^@]+$")
    password: constr(max_length=250)
    password_confirm: constr(max_length=250)
    is_google: bool
    is_active: bool
    scopes: Optional[List[constr(max_length=50)]]

    @validator('password_confirm')
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
    scopes: Optional[List[constr(max_length=50)]]

    @validator('password_confirm')
    def passwords_match(cls, value, values, **kwargs):
        if 'password' in values and value != values['password']:
            raise ValueError('passwords do not match')
        return value


class Ore(BaseModel):
    """
    Response schema for results from database
    """
    id: int
    name: str
    created: datetime
    updated: datetime

    class Config:
        orm_mode = True


class OreCreate(BaseModel):
    name: constr(max_length=50)


class OreUpdate(BaseModel):
    name: Optional[constr(max_length=50)]


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
    user: Related
    station: Related
    ore: Related
    method: Related
    created: datetime
    updated: datetime
    quantity: float
    duration: float

    class Config:
        orm_mode = True


class MiningSessionEntryCreate(BaseModel):
    user: Related
    station: Related
    ore: Related
    method: Related
    quantity: conint(gt=0)
    duration: constr(regex=r"^(?:(?P<days>\d\d?)[Dd])?\s*"
                           r"(?:(?P<hours>\d\d?)[Hh])?\s*"
                           r"(?:(?P<minutes>\d\d?)[Mm])?$")

    @validator("duration")
    def duration_parse(cls, value, values, field, **kwargs):
        match = field.type_.regex.match(value)
        seconds = (
                optint(match.group("days")) * 86400
                + optint(match.group("hours")) * 3600
                + optint(match.group("minutes")) * 60
        )
        return seconds


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


class MiningSessionInvite(BaseModel):
    id: int
    name: str
    created: datetime

    class Config:
        orm_mode = True


class MiningSessionWithUsersEntries(MiningSession):
    users_invited: List[MiningSessionInvite]
    entries: List[MiningSessionEntry]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(
            cls, obj: "screfinery.stores.model.MiningSession"
            ) -> "MiningSessionWithUsersEntries":
        return cls(
            id=obj.id,
            creator=obj.creator,
            name=obj.name,
            created=obj.created,
            updated=obj.updated,
            archived=obj.archived,
            yield_scu=obj.yield_scu,
            yield_uec=obj.yield_uec,
            users_invited=[
                MiningSessionInvite(
                    id=rel.user.id,
                    name=rel.user.name,
                    created=rel.created
                )
                for rel in obj.users_invited
            ],
            entries=obj.entries
        )


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

