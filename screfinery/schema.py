"""
Request and response object schemas with validation
- Classes ending in "Create" are used to validate request objects, which are to be
  added to the database.
- Classes ending in "Update" are used to validate request objects, which are to be
  updated in the database.
- Classes without "Create" or "Update" are used to describe the response objects.
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar, Any

from pydantic import BaseModel, validator, confloat, constr
from pydantic.generics import GenericModel


ItemT = TypeVar("ItemT")


class ListResponse(GenericModel, Generic[ItemT]):
    total_count: int
    items: list[ItemT]


class Login(BaseModel):
    username: str
    password: str


class UserScope(BaseModel):
    scope: str
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
    created: datetime
    updated: datetime
    last_login: Optional[datetime]
    scopes: list[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, user: "User") -> "User":
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
        )


class UserCreate(BaseModel):
    name: str
    mail: constr(regex=r"^[^@]+@[^@]+$")
    password: str
    password_confirm: str
    is_google: bool
    is_active: bool
    scopes: Optional[list[str]]

    @validator('password_confirm')
    def passwords_match(cls, value, values, **kwargs):
        if 'password' in values and value != values['password']:
            raise ValueError('passwords do not match')
        return value


class UserUpdate(BaseModel):
    name: Optional[str]
    mail: Optional[constr(regex=r"^[^@]+@[^@]+$")]
    password: Optional[str]
    password_confirm: Optional[str]
    is_google: Optional[bool]
    is_active: Optional[bool]
    scopes: Optional[list[str]]

    @validator('password_confirm')
    def passwords_match(cls, value, values, **kwargs):
        if 'password' in values and value != values['password']:
            raise ValueError('passwords do not match')
        return value


class UserQuery(BaseModel):
    id: Optional[int]
    name: Optional[str]
    mail: Optional[constr(regex=r"^[^@]+@[^@]+$")]
    is_google: Optional[bool]
    is_active: Optional[bool]
    created: Optional[datetime]
    updated: Optional[datetime]
    last_login: Optional[datetime]


class Related(BaseModel):
    """
    Generic model for N:M relations
    """
    id: int
    name: str

    class Config:
        orm_mode = True


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
    name: str


class OreUpdate(BaseModel):
    name: Optional[str]


class StationOreEfficiency(BaseModel):
    efficiency_bonus: float
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
    efficiencies: list[StationOreEfficiency]

    class Config:
        orm_mode = True


class StationCreate(BaseModel):
    name: str
    efficiencies: list[StationOreEfficiency]


class StationUpdate(BaseModel):
    name: Optional[str]
    efficiencies: Optional[list[StationOreEfficiency]]


class MethodOreEfficiency(BaseModel):
    efficiency: confloat(gt=0, le=1)
    duration: confloat(gt=0)
    ore_id: int
    ore_name: Optional[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any):
        return cls(
            efficiency=obj.efficiency,
            duration=obj.duration,
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
    efficiencies: list[MethodOreEfficiency]

    class Config:
        orm_mode = True


class MethodCreate(BaseModel):
    name: str
    efficiencies: list[MethodOreEfficiency]


class MethodUpdate(BaseModel):
    name: Optional[str]
    efficiencies: Optional[list[MethodOreEfficiency]]


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
    name: str


class MiningSessionUpdate(BaseModel):
    name: Optional[str]
    archived: Optional[datetime]
    yield_scu: Optional[float]
    yield_uec: Optional[float]
    users_invited: Optional[list[Related]]

