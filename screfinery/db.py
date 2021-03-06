from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import sessionmaker

from screfinery.stores.model import Base


def init(config: dict, create_all=False) -> tuple:
    engine = engine_from_config(config, prefix="")
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if create_all:
        Base.metadata.create_all(bind=engine)
    return engine, session_local


def dump_schema(config: dict) -> None:
    def _dump_executor(sql, *multiparams, **params):
        print(sql.compile(dialect=engine.dialect))
    engine = create_engine(config["url"], strategy="mock", executor=_dump_executor)
    Base.metadata.create_all(bind=engine, checkfirst=False)


def create_schema(config: dict) -> None:
    engine = engine_from_config(config, prefix="")
    Base.metadata.create_all(bind=engine)
