"""The startup migrator is the only one that runs in production.

Heroku's database was built by create_all(), so it has no alembic_version row
and `alembic upgrade head` dies on the initial migration (the tables already
exist). What actually runs on deploy is create_all(checkfirst=True) plus
_run_migrations() in the app lifespan. create_all adds new *tables* but never
new *columns*, so a column added to an existing table reaches production only
if it is listed in app.main._MIGRATIONS.

Missing one doesn't degrade a feature — every SELECT of that model names the
column, so the page 500s.
"""

import re
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, text

from app.database import Base
from app.main import _MIGRATIONS, _run_migrations
from app.models import *  # noqa: F401,F403 — register every model


def _alembic_added_columns() -> set[tuple[str, str]]:
    """Every (table, column) an Alembic migration adds to an existing table."""
    added = set()
    for path in Path("alembic/versions").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        # op.add_column('users', sa.Column('lifetime_coins', ...))
        for table, column in re.findall(
            r"add_column\(\s*['\"](\w+)['\"]\s*,\s*sa\.Column\(\s*['\"](\w+)['\"]",
            source,
        ):
            added.add((table, column))
        # batch_alter_table('session_questions') as batch: batch.add_column(...)
        for batch_table, body in re.findall(
            r"batch_alter_table\(\s*['\"](\w+)['\"].*?\n((?:\s{8,}.*\n)+)", source
        ):
            for column in re.findall(
                r"add_column\(\s*sa\.Column\(\s*['\"](\w+)['\"]", body
            ):
                added.add((batch_table, column))
    return added


def test_every_alembic_added_column_also_runs_at_startup():
    listed = {(table, column) for table, column, _type, _default in _MIGRATIONS}
    added = _alembic_added_columns()
    assert added, "found no add_column calls — the parser has drifted"

    missing = added - listed
    assert not missing, (
        "these columns reach a fresh database but never an existing one: "
        f"{sorted(missing)} — add them to app.main._MIGRATIONS"
    )


def test_startup_brings_a_deployed_database_up_to_the_models(tmp_path):
    """Build the schema a deployed database actually has — the models minus
    every column _MIGRATIONS is responsible for — then assert the startup path
    brings it back up to what the models expect.

    This checks that each listed ALTER actually works (right type, valid
    default). An *omission* from the list is caught by the test above, not
    here: a column that isn't listed is never dropped from the shape either.
    """
    db_path = tmp_path / "deployed.db"
    engine = create_engine(f"sqlite:///{db_path}")

    listed = {(table, column) for table, column, _type, _default in _MIGRATIONS}
    deployed = MetaData()
    for table in Base.metadata.tables.values():
        # A column carries its own ForeignKey, so dropping it drops that too.
        Table(
            table.name,
            deployed,
            *[
                column._copy()
                for column in table.columns
                if (table.name, column.name) not in listed
            ],
        )
    deployed.create_all(bind=engine)

    _run_migrations(engine)

    with engine.connect() as conn:
        for name in {table for table, _c, _t, _d in _MIGRATIONS}:
            have = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info({name})"))
            }
            want = {c.name for c in Base.metadata.tables[name].columns}
            assert want <= have, f"{name} is missing {sorted(want - have)}"
