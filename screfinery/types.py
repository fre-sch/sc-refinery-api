from typing import Protocol, Type, List, Optional

from sqlalchemy.orm import Session


class Store(Protocol):

    def get_by_id(self, db: Session, id: int) -> Optional[Type]:
        pass

    def list_all(self, db: Session, offset: int, limit: int,
                 filter_: dict, sort: dict) -> List[Type]:
        pass

    def create_one(self, db: Session, data: Type) -> Optional[Type]:
        pass

    def update_by_id(self, db: Session, id: int, data: Type) -> Optional[Type]:
        pass

    def delete_by_id(self, db: Session, id: int) -> Optional[Type]:
        pass

    resource_name: str