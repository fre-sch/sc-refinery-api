from screfinery.basestore import BaseStore
from screfinery.storage.table import UserPerm


class UserPermStore(BaseStore):
    def __init__(self):
        super().__init__(UserPerm)

    @property
    def primary_key(self):
        return self.table.user_id