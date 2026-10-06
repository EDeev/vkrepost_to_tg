# Portal in VK

**Русский** · [English](README.en.md)

[![CI](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/ci.yml/badge.svg)](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/ci.yml)
[![Docker](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/docker.yml/badge.svg)](https://github.com/EDeev/vkrepost_to_tg/actions/workflows/docker.yml)
[![License](https://img.shields.io/github/license/EDeev/vkrepost_to_tg)](LICENSE)

Telegram-бот, который пересылает новые посты со страниц и сообществ ВКонтакте в Telegram: подписываешься
командой `/add <короткое имя>`, и каждый новый пост приходит сообщением — с фото, обложками видео,
документами, аудио, опросами и репостами.

**Статус:** личный проект, завершён · бот [@vkportalbot](https://t.me/vkportalbot)

**Стек:** Python 3.12 · aiogram 3 · vk_api · PostgreSQL · Docker

## Возможности

- До 10 подписок на пользователя: личные страницы, группы и паблики
- Пост переводится в формат Telegram:
  - фото, обложки видео и картинки-документы — альбомом;
  - аудио — отдельным сообщением;
  - опросы, ссылки и документы — в тексте;
  - упоминания `[id1|Имя]` — ссылками;
  - у репостов — оба автора и комментарий.
- Ограничения Telegram учтены: одиночное фото, альбомы до 10 элементов, длинный текст отдельными
  сообщениями
- `/last_post` — последний пост любой страницы, `/update` — прислать пост заново с актуальными данными
- Свой токен VK (необязательно) даёт посты закрытых страниц, на которые вы подписаны, и лайки из Telegram
  (`/like` ответом на пост)

> [!IMPORTANT]
> Если вы присылаете боту свой токен VK, он хранится на сервере бота. Удалить его можно командой
> `/logout`, полностью отозвать доступ — в настройках VK, раздел «Приложения и сайты».

## Запуск

```bash
git clone https://github.com/EDeev/vkrepost_to_tg.git && cd vkrepost_to_tg
cp .env.example .env      # BOT_TOKEN и сервисный ключ приложения VK
docker compose up -d
```

Готовый образ: `docker pull ghcr.io/edeev/vkrepost_to_tg` или `docker pull git.deev.su/edeev/vkrepost_to_tg`.
Таблицы в PostgreSQL создаются при первом запуске. Данные старой версии (SQLite `users.db` и `base.db`)
переносит `python scripts/migrate_sqlite.py --sqlite-dir путь/к/db --dsn postgresql://…`.

Без Docker: Python 3.12, `pip install -r requirements.txt`, затем
`cd code && BOT_TOKEN=… VK_SERVICE_TOKEN=… DATABASE_URL=postgresql://… python bot.py` (нужен PostgreSQL).

## Как устроено

```
code/bot.py          запуск и фоновый опрос подписок раз в минуту
code/handlers.py     команды: подписки, последний пост, лайки, токен VK
code/vk_scripts.py   запросы к VK API и разбор поста
code/scripts.py      пост → текст в HTML и медиа Telegram, отправка с учётом ограничений
code/sql.py          пользователи, подписки и последний пост каждой страницы (PostgreSQL)
scripts/             перенос данных из SQLite
```

Для закрытой страницы бот берёт токен одного из её подписчиков, для открытых — сервисный ключ. Запросы
к VK идут в отдельном потоке, чтобы бот не замирал. Текст из ВК экранируется.

## Разработка

```bash
pip install -r requirements-dev.txt
ruff check --select E9,F code tests && pytest
```

Тесты проверяют разбор постов (экранирование, упоминания, ссылки, репосты, лимит альбома) и отправку
(одиночное фото, длинный текст, аудио). Docker-образ собирается по тегу `v*` и публикуется в GitHub
Packages и `git.deev.su`.

## Лицензия

MIT — см. [LICENSE](LICENSE).

## Автор

**Деев Егор Викторович** — [GitHub](https://github.com/EDeev) · [Telegram](https://t.me/DeevEgor) · [egor@deev.space](mailto:egor@deev.space)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звёздочку на GitHub!</sub>
  <p><sub>Сделано с ❤️ — <a href="https://deev.space">deev.space</a></sub></p>
</div>
