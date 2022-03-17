from screfinery.basestore import BaseStore
from screfinery.storage.table import MiningSession


class MiningSessionStore(BaseStore):
    def __init__(self):
        super().__init__(MiningSession)


def mining_session_validate(data, case):
    pass