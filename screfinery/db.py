from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from screfinery.stores.model import Base


def init(config) -> tuple:
    engine = engine_from_config(config.db, prefix="")
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, session_local
