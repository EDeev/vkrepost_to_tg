import os
import sqlite3
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

DSN = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="нужен TEST_DATABASE_URL (PostgreSQL)")


@pytest.fixture
def pool():
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    import sql
    p = sql.connect(DSN)
    yield p
    p.close()


def test_subscriptions(pool):
    from sql import Base, Users
    du, db = Users(pool), Base(pool)
    du.add_user(111)
    uid = du.get_user_id(111)
    db.add_infoUser(uid)
    du.add_group(-500)
    gid = du.get_group_id(-500)
    db.add_infoGroup(gid, 1, 42)
    db.update_user_groups(uid, str(gid))
    db.update_countUser(uid, 1)
    db.update_countGroup(gid, 1)
    assert db.all_subUser() == [(uid, str(gid))] and db.all_activUser() == []
    db.update_token(uid, "tok")
    assert db.all_activUser() == [(uid, str(gid))]
    assert db.all_notifGroup() == [(gid,)] and db.get_postGroup(gid) == 42 and du.get_vk_id(gid) == -500
    db.update_status(uid)
    assert db.get_status(uid) is False and db.all_subUser() == []


def test_migration(pool, tmp_path):
    import migrate_sqlite
    users = sqlite3.connect(tmp_path / "users.db")
    users.executescript("""
        CREATE TABLE user (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL);
        CREATE TABLE "group" (id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL);
        INSERT INTO user VALUES (3, 333);
        INSERT INTO "group" VALUES (7, -700);
    """)
    users.commit()
    base = sqlite3.connect(tmp_path / "base.db")
    base.executescript("""
        CREATE TABLE user (user_id INTEGER NOT NULL, status BOOLEAN NOT NULL DEFAULT (True), count INTEGER NOT NULL DEFAULT (0),
                           groups TEXT, token TEXT);
        CREATE TABLE "group" (group_id INTEGER NOT NULL, type BOOLEAN NOT NULL, count INTEGER NOT NULL DEFAULT (0),
                              last_post INTEGER NOT NULL);
        INSERT INTO user VALUES (3, 1, 1, '7', NULL);
        INSERT INTO "group" VALUES (7, 1, 1, 99);
    """)
    base.commit()
    assert migrate_sqlite.migrate(str(tmp_path), DSN, force=True)

    from sql import Base, Users
    du, db = Users(pool), Base(pool)
    assert du.get_user_id(333) == 3 and du.get_group_id(-700) == 7
    assert db.get_user_groups(3) == "7" and db.get_postGroup(7) == 99
    du.add_group(-800)
    assert du.get_group_id(-800) == 8
