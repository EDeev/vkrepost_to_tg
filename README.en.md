# Portal in VK

[Русский](README.md) · **English**

[![CI](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/ci.yml/badge.svg)](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/ci.yml)
[![Docker](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/docker.yml/badge.svg)](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/docker.yml)
[![License](https://img.shields.io/github/license/EDeev/vkrepost_to_tg)](LICENSE)

A Telegram bot that forwards new posts from VK (VKontakte) pages and communities to Telegram: subscribe
with `/add <short name>` and every new post arrives as a message, with photos, video covers, documents,
audio, polls and reposts. The bot speaks Russian.

**Status:** personal project, completed · bot [@vkportalbot](https://t.me/vkportalbot)

**Stack:** Python 3.12 · aiogram 3 · vk_api · PostgreSQL · Docker

## Features

- Up to 10 subscriptions per user: personal pages, groups and public pages
- A post is converted to Telegram format:
  - photos, video covers and image documents — as an album;
  - audio — as a separate message;
  - polls, links and documents — in the text;
  - `[id1|Name]` mentions — as links;
  - reposts show both authors and the comment.
- Telegram limits are handled: a single photo, albums up to 10 items, long text as separate messages
- `/last_post` — the latest post of any page; `/update` — resend a post with fresh data
- Your own VK token (optional) gives posts from closed pages you follow and likes from Telegram (`/like`
  as a reply to a post)

> [!IMPORTANT]
> If you send the bot your VK token, it is stored on the bot's server. Delete it with `/logout`; revoke
> access completely in VK settings, "Apps and websites".

## Running

```bash
git clone https://github.com/EDeev/vkrepost_to_tg.git && cd vkrepost_to_tg
cp .env.example .env      # BOT_TOKEN and the VK app service key
docker compose up -d
```

Prebuilt image: `docker pull ghcr.io/edeev/vkrepost_to_tg` or `docker pull git.deev.su/edeev/vkrepost_to_tg`.
PostgreSQL tables are created on first start. Data from the old version (SQLite `users.db` and `base.db`)
is moved by `python scripts/migrate_sqlite.py --sqlite-dir path/to/db --dsn postgresql://…`.

Without Docker: Python 3.12, `pip install -r requirements.txt`, then
`cd code && BOT_TOKEN=… VK_SERVICE_TOKEN=… DATABASE_URL=postgresql://… python bot.py` (needs PostgreSQL).

## How it works

```
code/bot.py          entry point and background polling of subscriptions every minute
code/handlers.py     commands: subscriptions, latest post, likes, VK token
code/vk_scripts.py   VK API requests and post parsing
code/scripts.py      post → HTML text and Telegram media, sending within Telegram limits
code/sql.py          users, subscriptions and each page's latest post (PostgreSQL)
scripts/             migration from SQLite
```

For a closed page the bot uses the token of one of its subscribers; for open pages, the service key. VK
requests run in a separate thread so the bot never freezes. Text from VK is escaped.

## Development

```bash
pip install -r requirements-dev.txt
ruff check --select E9,F code tests && pytest
```

The tests cover post parsing (escaping, mentions, links, reposts, album limit) and sending (single photo,
long text, audio). The Docker image is built on `v*` tags and published to GitHub Packages and
`git.deev.su`.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Egor Deev** — [GitHub](https://github.com/EDeev) · [Telegram](https://t.me/DeevEgor) · [egor@deev.space](mailto:egor@deev.space)

---

<div align="center">
  <sub>⭐ If you find this project useful, give it a star on GitHub!</sub>
  <p><sub>Made with ❤️ — <a href="https://deev.space">deev.space</a></sub></p>
</div>
