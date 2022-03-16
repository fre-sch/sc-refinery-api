from screfinery.basestore import BaseStore
from screfinery.storage.table import UserSession


class UserSessionStore(BaseStore):
    def __init__(self):
        super().__init__(UserSession)