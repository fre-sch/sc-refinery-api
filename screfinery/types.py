from typing import Protocol, Type

from sqlalchemy.orm import Session


class Store(Protocol):

    def get_by_id(self, db: Session, id: int) -> Type:
        pass

    def list_all(self, db: Session, offset: int, limit: int) -> Type:
        pass

    def create_one(self, db: Session, data: Type) -> Type:
        pass

    def update_by_id(self, db: Session, id: int, data: Type) -> Type:
        pass

    def delete_by_id(self, db: Session, id: int) -> Type:
        pass

    resource_name: str