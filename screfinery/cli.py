import os

import click

from screfinery import db
from screfinery.config import load_config
from screfinery.schema import UserCreate, UserQuery
from screfinery.stores import user_store


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    config_path = os.environ["CONFIG_PATH"]
    config = load_config(config_path)
    ctx.obj["config"] = config


@main.command()
@click.pass_context
def dump_schema(ctx):
    config = ctx.obj["config"]
    db.dump_schema(config.app.db)


@main.group()
def user():
    pass


@user.command("create")
@click.argument("name")
@click.argument("mail")
@click.argument("password")
@click.argument("permissions")
@click.pass_context
def user_create(ctx, name, mail, password, permissions):
    config = ctx.obj["config"].app
    user = UserCreate(
        name=name,
        mail=mail,
        password=password,
        password_confirm=password,
        is_google=False,
        is_active=True,
        scopes=[it.strip() for it in permissions.split(",")]
    )
    _, session = db.init(config.db, config.env == "dev")

    with session() as db_session:
        user_store.create_one(db_session, user, config.password_salt)


if __name__ == "__main__":
    main()
