from html import escape

from aiogram import types

import config

CAPTION_LIMIT = 1024  # подпись к фото в Telegram
TEXT_LIMIT = 4096     # обычное сообщение


def login(user_id, du, db):
    user_id = int(user_id)
    if not du.user_exists(user_id): du.add_user(user_id)

    user_id = du.get_user_id(user_id)
    if not db.infoUser_exists(user_id): db.add_infoUser(user_id)

    return user_id


def pars_post(output):
    """Пост из vk_scripts.get_output → текст в HTML, аудио и медиа для Telegram.
    Всё, что пришло из ВК, экранируется: «<» или «&» в посте иначе ломают отправку"""
    media, video, url, audio, poll, link = [], [], [], [], [], []

    for group in output[0]:
        if group[0] == "poll": poll = group[1]
        elif group[0] == "link": link.append(group[1])
        elif group[0] == "video": video.append(group[1])
        elif group[0] == "doc" and group[1][2] != 4: url.append([group[1][0], group[1][1], group[1][3]])
        elif group[0] == "audio": audio.append(types.InputMediaAudio(
            media=group[1][1], caption=f"<b>Название: {escape(group[1][0])} / Автор: {escape(group[1][2])}</b>"))

    if output[1] != "":
        # упоминания ВК вида [id1|Имя] превращаются в ссылки
        post = [elem_2 for elem_1 in escape(output[1], quote=False).split("[") for elem_2 in elem_1.split("]")]
        for i, elem in enumerate(post):
            if "|" in elem and i != 0:
                elem = elem.split("|", 1)
                post[i] = f"<a href='https://vk.com/{escape(elem[0])}'>{elem[1]}</a>"

        text = f"{output[2]}\n\n{''.join(post)}\n"
    else: text = f"{output[2]}\n"

    if poll:
        text += (f"\n<b>> Проводится</b> {config.anonymous[poll[3]]} {config.unvote[poll[2]]}! "
                 f"<b>Вопрос:</b> {escape(poll[0])} <b>[{poll[1]}]</b>\n")
        text += ''.join([f'<b>{i + 1}. Ответ:</b> {escape(ans[0])} <b>[{ans[1]}]</b>\n'
                         for i, ans in enumerate(poll[4])]) + "\n"

    if video:
        for frame in video:
            text += f"\n<b>Видео</b> <i>« {escape(frame[0])} »</i>\n"

            k, dura = 0, frame[1]
            if dura > 60: dura, k = dura // 60, 1

            text += f"<b>Длительность:</b> {dura} {config.dura[k]}; <b>Просмотров:</b> {frame[2]};\n"

    if url:
        for data in url:
            k, dt = 0, data[2]
            while dt > 1024 and k < len(config.data) - 1:
                dt, k = dt // 1024, k + 1
            text += (f"\n<b>Документ - [</b> <a href='{escape(data[1])}'>{escape(data[0])}</a> "
                     f"({dt} {config.data[k]}) <b>]</b>")
        text += "\n"

    if link:
        text += ''.join([f"\n<b>Ссылка - [</b> <a href='{escape(s[1])}'>{escape(s[0])}</a> <b>]</b>"
                         for s in link]) + "\n"
    if audio: text += '\n<b>« Также присутствуют аудио файлы »</b>'

    for group in output[0]:
        if group[0] == "photo":
            media.append(types.InputMediaPhoto(media=group[1]))
        elif group[0] == "video" and group[1][3]:  # у видео может не быть обложки
            media.append(types.InputMediaPhoto(media=group[1][3]))
        elif group[0] == "doc" and group[1][2] == 4:
            media.append(types.InputMediaPhoto(media=group[1][1]))

    return text, audio[:10], media[:10]  # в одном альбоме Telegram не больше 10 элементов


def split_text(text, limit=TEXT_LIMIT):
    """Делит длинный текст по строкам, чтобы не разрывать HTML-теги посередине"""
    parts, current = [], ""
    for line in text.split("\n"):
        while len(line) > limit:  # одна строка длиннее лимита — режем как есть
            if current: parts.append(current); current = ""
            parts.append(line[:limit]); line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            parts.append(current); current = ""
        current += line + "\n"
    if current.strip(): parts.append(current)
    return parts


async def send_post(bot, chat_id, text, audio, media):
    """Отправляет пост с учётом ограничений Telegram: альбом — от 2 до 10 элементов, подпись —
    до 1024 символов, сообщение — до 4096"""
    first = None

    if media:
        caption = text if len(text) <= CAPTION_LIMIT else None
        if len(media) == 1:
            first = await bot.send_photo(chat_id=chat_id, photo=media[0].media, caption=caption)
        else:
            media[0].caption = caption
            first = (await bot.send_media_group(chat_id=chat_id, media=media))[0]
        if caption is None:
            for part in split_text(text):
                await bot.send_message(chat_id=chat_id, text=part, disable_web_page_preview=True,
                                       reply_to_message_id=first.message_id)
    else:
        for part in split_text(text):
            sent = await bot.send_message(chat_id=chat_id, text=part, disable_web_page_preview=True)
            first = first or sent

    if audio:
        reply_to = first.message_id if first else None
        if len(audio) == 1:
            await bot.send_audio(chat_id=chat_id, audio=audio[0].media, caption=audio[0].caption,
                                 reply_to_message_id=reply_to)
        else:
            await bot.send_media_group(chat_id=chat_id, media=audio, reply_to_message_id=reply_to)
