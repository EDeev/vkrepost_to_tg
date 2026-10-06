"""Хранилище бота — PostgreSQL (до 2026-10 — два файла SQLite users.db и base.db).

users и pages хранят короткие внутренние номера пользователей Telegram и страниц ВК; subscribers и
page_state ссылаются на эти номера, как раньше таблицы user и group в base.db (в PostgreSQL имена
user и group зарезервированы)."""
from psycopg_pool import ConnectionPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id    SERIAL PRIMARY KEY,
    tg_id BIGINT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS pages (
    id    SERIAL PRIMARY KEY,
    vk_id BIGINT NOT NULL UNIQUE               -- у сообществ отрицательный
);
CREATE TABLE IF NOT EXISTS subscribers (
    user_id INTEGER PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    status  BOOLEAN NOT NULL DEFAULT TRUE,     -- получает ли посты
    count   INTEGER NOT NULL DEFAULT 0,        -- число подписок
    groups  TEXT,                              -- номера страниц через «;»
    token   TEXT                               -- токен VK пользователя (необязательный)
);
CREATE TABLE IF NOT EXISTS page_state (
    page_id   INTEGER PRIMARY KEY REFERENCES pages (id) ON DELETE CASCADE,
    type      BOOLEAN NOT NULL,                -- TRUE — сообщество, FALSE — личная страница
    count     INTEGER NOT NULL DEFAULT 0,      -- сколько подписчиков ждут посты
    last_post BIGINT NOT NULL
);
"""


def connect(dsn):
    """Пул соединений сам переподключается, если PostgreSQL перезапускали"""
    pool = ConnectionPool(dsn, min_size=1, max_size=4, kwargs={"autocommit": True}, open=True)
    with pool.connection() as conn:
        conn.execute(SCHEMA)
    return pool


class _Base:
    def __init__(self, pool):
        self.pool = pool

    def _one(self, query, args=()):
        with self.pool.connection() as conn:
            row = conn.execute(query, args).fetchone()
            return row[0] if row else None

    def _all(self, query, args=()):
        with self.pool.connection() as conn:
            return conn.execute(query, args).fetchall()

    def _run(self, query, args=()):
        with self.pool.connection() as conn:
            conn.execute(query, args)


class Users(_Base):
    # ПОЛЬЗОВАТЕЛИ TELEGRAM
    def user_exists(self, user_id):
        return bool(self._one("SELECT 1 FROM users WHERE tg_id = %s", (user_id,)))

    def add_user(self, user_id):
        self._run("INSERT INTO users (tg_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

    def get_user_id(self, user_id):
        """Внутренний номер по id Telegram"""
        return self._one("SELECT id FROM users WHERE tg_id = %s", (user_id,))

    def get_tg_id(self, user_id):
        """id Telegram по внутреннему номеру"""
        return self._one("SELECT tg_id FROM users WHERE id = %s", (user_id,))

    # СТРАНИЦЫ ВК
    def group_exists(self, group_id):
        return bool(self._one("SELECT 1 FROM pages WHERE vk_id = %s", (group_id,)))

    def add_group(self, group_id):
        self._run("INSERT INTO pages (vk_id) VALUES (%s) ON CONFLICT DO NOTHING", (group_id,))

    def get_group_id(self, group_id):
        """Внутренний номер страницы по id ВК"""
        return self._one("SELECT id FROM pages WHERE vk_id = %s", (group_id,))

    def get_vk_id(self, group_id):
        """id ВК по внутреннему номеру"""
        return self._one("SELECT vk_id FROM pages WHERE id = %s", (group_id,))


class Base(_Base):
    # ПОДПИСЧИКИ
    def infoUser_exists(self, user_id):
        return bool(self._one("SELECT 1 FROM subscribers WHERE user_id = %s", (user_id,)))

    def add_infoUser(self, user_id):
        self._run("INSERT INTO subscribers (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

    def all_activUser(self):
        """Подписчики со своим токеном VK, которые получают посты"""
        return self._all("SELECT user_id, groups FROM subscribers WHERE status AND count > 0 AND token IS NOT NULL")

    def all_subUser(self):
        """Все подписчики, которые получают посты"""
        return self._all("SELECT user_id, groups FROM subscribers WHERE status AND count > 0")

    def get_status(self, user_id):
        return self._one("SELECT status FROM subscribers WHERE user_id = %s", (user_id,))

    def update_status(self, user_id):
        self._run("UPDATE subscribers SET status = NOT status WHERE user_id = %s", (user_id,))

    def get_user_groups(self, user_id):
        return self._one("SELECT groups FROM subscribers WHERE user_id = %s", (user_id,))

    def update_user_groups(self, user_id, groups):
        self._run("UPDATE subscribers SET groups = %s WHERE user_id = %s", (groups, user_id))

    def get_token(self, user_id):
        return self._one("SELECT token FROM subscribers WHERE user_id = %s", (user_id,))

    def update_token(self, user_id, token):
        self._run("UPDATE subscribers SET token = %s WHERE user_id = %s", (token, user_id))

    def get_countUser(self, user_id):
        return self._one("SELECT count FROM subscribers WHERE user_id = %s", (user_id,))

    def update_countUser(self, user_id, num):
        self._run("UPDATE subscribers SET count = count + %s WHERE user_id = %s", (num, user_id))

    # СТРАНИЦЫ
    def infoGroup_exists(self, group_id):
        return bool(self._one("SELECT 1 FROM page_state WHERE page_id = %s", (group_id,)))

    def add_infoGroup(self, group_id, tp, last_post):
        self._run("INSERT INTO page_state (page_id, type, last_post) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                  (group_id, bool(tp), last_post))

    def all_notifGroup(self):
        """Страницы, на которые кто-то подписан"""
        return self._all("SELECT page_id FROM page_state WHERE count > 0")

    def get_postGroup(self, group_id):
        return self._one("SELECT last_post FROM page_state WHERE page_id = %s", (group_id,))

    def update_postGroup(self, group_id, last_post):
        self._run("UPDATE page_state SET last_post = %s WHERE page_id = %s", (last_post, group_id))

    def update_countGroup(self, group_id, num):
        self._run("UPDATE page_state SET count = count + %s WHERE page_id = %s", (num, group_id))
