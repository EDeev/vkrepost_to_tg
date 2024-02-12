import config


def login(user_id, du, db):
    user_id = int(user_id)
    if not du.user_exists(user_id): du.add_user(user_id)

    user_id = du.get_user_id(user_id)
    if not db.infoUser_exists(user_id): db.add_infoUser(user_id)

    return user_id


def pars_post(types, output):
    media, ttl, url, audio, poll, link = [], [], [], [], [], []

    for group in output[0]:
        if group[0] == "poll": poll = group[1]
        elif group[0] == "link": link.append(group[1])
        elif group[0] == "video": ttl.append(group[1])
        elif group[0] == "doc" and group[1][2] != 4: url.append([group[1][0], group[1][1], group[1][3]])
        elif group[0] == "audio": audio.append(types.InputMediaAudio(media=group[1][1], parse_mode=types.ParseMode.MARKDOWN,
                                                                     caption=f"*Название: {group[1][0]} / Автор: {group[1][2]}*"))

    if output[1] != "": text = f"{output[2]}\n\n*{output[1]}*\n"
    else: text = f"{output[2]}\n"

    if poll:
        text += f"\n*> Проводиться {config.anonymous[poll[3]]} {config.unvote[poll[2]]}!"
        text += f"*\n*---------------------*\n*- Вопрос: {poll[0]} [{poll[1]}]*\n"
        text += ''.join([f'*{i}. Ответ: {ans[0]} [{ans[1]}]*\n' for i, ans in enumerate(poll[4])])
        text += "*---------------------*\n"

    if ttl: text += f"\n*Видео -* находятся в оригинальном посте в количестве {len(ttl)} записей\n"

    if url:
        for data in url:
            k, dt = 0, data[2]
            while True:
                if dt > 1024: dt = dt // 1024; k += 1
                else: break
            text += f"\n*Документ - [* [{data[0]}]({data[1]}) ({dt} {config.data[k]}) *]*"
        text += "\n"

    if link: text += ''.join([f"\n*Ссылка - [* [{s[0]}]({s[1]}) *]*" for s in link]) + "\n"
    if audio: text += '\n*« Также присутствуют аудио файлы »*'

    for i, group in enumerate(output[0]):
        if group[0] == "photo":
            if i: media.append(types.InputMediaPhoto(media=group[1]))
            else: media.append(types.InputMediaPhoto(media=group[1], caption=text, parse_mode=types.ParseMode.MARKDOWN))
        elif group[0] == "doc":
            if group[1][2] == 4:
                if i: media.append(types.InputMediaPhoto(media=group[1][1]))
                else: media.append(types.InputMediaPhoto(media=group[1][1], caption=text, parse_mode=types.ParseMode.MARKDOWN))

    return text, audio, media
