import aiosqlite
import click
import asyncio

from pypika import Criterion

from screfinery import storage
from screfinery.storage import table
from screfinery.util import load_config
from screfinery.validation import InvalidDataError


async def init_db(config):
    db_url = config["db"].get("url")
    if db_url.startswith("sqlite"):
        db = await aiosqlite.connect(db_url)
        db.row_factory = aiosqlite.Row
        return db


async def db_create_user(config, user_data):
    db = await init_db(config)
    user_store = storage.UserStore()

    user_ = await user_store.create(db, user_data)

    if user_ is not None:
        click.echo(f"user {user_['id']} created")

    await db.close()


async def db_delete_user(config, user_id, user_mail):
    db = await init_db(config)
    user_store = storage.UserStore()
    user_ = await user_store.find_one(db, Criterion.all([
        table.User.id == user_id,
        table.User.mail == user_mail
    ]))
    if user is not None:
        await user_store.remove_id(db, user_["id"])
        click.echo(f"user ({user_['id']}, {user_['mail']}) deleted")
    else:
        click.echo(f"no such user ({user_['id']}, {user_['mail']})")
    await db.close()


def run_async(coroutine):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coroutine)
    finally:
        pass


@click.group()
@click.option("--config-path", type=click.Path(exists=True))
@click.pass_context
def main(ctx, config_path):
    if config_path is None:
        config_path = "config.ini"
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path)


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
    user_data = {
        "name": name,
        "mail": mail,
        "password": password,
        "password_confirm": password,
        "scopes": [it.strip() for it in permissions.split(",")]
    }
    try:
        user_data = storage.user_validator(ctx.obj["config"], user_data, "create")
    except InvalidDataError as exc:
        click.echo(f"{exc}: {exc.errors}")
        exit(1)
    run_async(db_create_user(ctx.obj["config"], user_data))


@user.command("delete")
@click.argument("user_id")
@click.argument("user_mail")
@click.pass_context
def user_delete(ctx, user_id, user_mail):
    run_async(db_delete_user(ctx.obj["config"], user_id, user_mail))


if __name__ == "__main__":
    main()
