"""Перенос данных Portal in VK из SQLite (users.db, base.db) в PostgreSQL.

    python scripts/migrate_sqlite.py --sqlite-dir /path/to/db --dsn postgresql://…

Внутренние номера пользователей и страниц сохраняются: на них ссылаются списки подписок.
"""
import argparse
import os
import sqlite3
import sys

import psycopg

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from sql import SCHEMA  # noqa: E402


def migrate(sqlite_dir, dsn, force=False):
    users_db = sqlite3.connect(os.path.join(sqlite_dir, "users.db"))
    base_db = sqlite3.connect(os.path.join(sqlite_dir, "base.db"))

    users = users_db.execute("SELECT id, user_id FROM user ORDER BY id").fetchall()
    pages = users_db.execute('SELECT id, group_id FROM "group" ORDER BY id').fetchall()
    subs = base_db.execute("SELECT user_id, status, count, groups, token FROM user").fetchall()
    states = base_db.execute('SELECT group_id, type, count, last_post FROM "group"').fetchall()
    known_users, known_pages = {u[0] for u in users}, {p[0] for p in pages}

    with psycopg.connect(dsn) as conn:
        conn.execute(SCHEMA)
        if conn.execute("SELECT count(*) FROM users").fetchone()[0]:
            if not force:
                raise SystemExit("В PostgreSQL уже есть данные — перенос остановлен (--force очистит таблицы)")
            conn.execute("TRUNCATE users, pages, subscribers, page_state RESTART IDENTITY CASCADE")
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO users (id, tg_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", users)
            cur.executemany("INSERT INTO pages (id, vk_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", pages)
            cur.executemany("INSERT INTO subscribers (user_id, status, count, groups, token) VALUES (%s, %s, %s, %s, %s) "
                            "ON CONFLICT DO NOTHING",
                            [(u, bool(s), c or 0, g, t) for u, s, c, g, t in subs if u in known_users])
            cur.executemany("INSERT INTO page_state (page_id, type, count, last_post) VALUES (%s, %s, %s, %s) "
                            "ON CONFLICT DO NOTHING",
                            [(p, bool(tp), c or 0, lp) for p, tp, c, lp in states if p in known_pages])
            for table in ("users", "pages"):
                cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                            f"GREATEST((SELECT max(id) FROM {table}), 1))")
        report = {name: (src, conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0])
                  for name, src in (("users", len(users)), ("pages", len(pages)),
                                    ("subscribers", len(subs)), ("page_state", len(states)))}

    for name, (src, dst) in report.items():
        print(f"{name:11} SQLite {src:>5}  PostgreSQL {dst:>5}  {'ok' if src == dst else 'MISMATCH'}")
    return all(a == b for a, b in report.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sqlite-dir", required=True)
    parser.add_argument("--dsn", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    sys.exit(0 if migrate(args.sqlite_dir, args.dsn, args.force) else 1)


if __name__ == "__main__":
    main()
