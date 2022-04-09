import json
from logging.config import dictConfig
from typing import Optional, Any

import yaml
from pydantic import BaseModel


class GoogleConfig(BaseModel):
    client_id: str
    certs_path: str
    certs: Optional[dict] = None


class AppConfig(BaseModel):
    password_salt: str
    db: dict
    google: Optional[GoogleConfig] = None


class Config(BaseModel):
    app: AppConfig
    logging: Optional[dict] = None
    ## set env=dev to enable debug, verbose output, and database creation
    env: Optional[str] = "production"


def load_config(path: str) -> Config:
    with open(path, "r") as fp:
        config_dict = yaml.safe_load(fp)
    config = Config.parse_obj(config_dict)
    if config.logging is not None:
        dictConfig(config.logging)
    if config.app.google and config.app.google.certs_path:
        with open(config.app.google.certs_path, "r") as fp:
            config.app.google.certs = json.load(fp)
    return config
