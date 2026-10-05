import config


def login(user_id, du, db):
    user_id = int(user_id)
    if not du.user_exists(user_id): du.add_user(user_id)

    user_id = du.get_user_id(user_id)
    if not db.infoUser_exists(user_id): db.add_infoUser(user_id)

    return user_id


def pars_post(types, output):
    media, video, url, audio, poll, link = [], [], [], [], [], []

    for group in output[0]:
        if group[0] == "poll": poll = group[1]
        elif group[0] == "link": link.append(group[1])
        elif group[0] == "video": video.append(group[1])
        elif group[0] == "doc" and group[1][2] != 4: url.append([group[1][0], group[1][1], group[1][3]])
        elif group[0] == "audio": audio.append(types.InputMediaAudio(
            media=group[1][1], caption=f"<b>Название: {group[1][0]} / Автор: {group[1][2]}</b>"))

    if output[1] != "":
        post = [elem_2 for elem_1 in output[1].split("[") for elem_2 in elem_1.split("]")]
        for i, elem in enumerate(post):
            if "|" in elem and i != 0:
                elem = elem.split("|")
                post[i] = f"<a href='https://vk.com/{elem[0]}'>{elem[1]}</a>"

        text = f"{output[2]}\n\n{''.join(post)}\n"
    else: text = f"{output[2]}\n"

    if poll:
        text += f"\n<b>> Проводиться</b> {config.anonymous[poll[3]]} {config.unvote[poll[2]]}! <b>Вопрос:</b> {poll[0]} <b>[{poll[1]}]</b>\n"
        text += ''.join([f'<b>{i + 1}. Ответ:</b> {ans[0]} <b>[{ans[1]}]</b>\n' for i, ans in enumerate(poll[4])]) + "\n"

    if video:
        for frame in video:
            text += f"\n<b>Видео</b> <i>« {frame[0]} »</i>\n"

            k, dura = 0, frame[1]
            while k < 1:
                if dura > 60: dura = dura // 60; k += 1
                else: break

            text += f"<b>Длительность:</b> {dura} {config.dura[k]}; <b>Лайков:</b> {frame[2]};\n"

    if url:
        for data in url:
            k, dt = 0, data[2]
            while True:
                if dt > 1024: dt = dt // 1024; k += 1
                else: break
            text += f"\n<b>Документ - [</b> <a href='{data[1]}'>{data[0]}</a> ({dt} {config.data[k]}) <b>]</b>"
        text += "\n"

    if link: text += ''.join([f"\n<b>Ссылка - [</b> [{s[0]}]({s[1]}) <b>]</b>" for s in link]) + "\n"
    if audio: text += '\n<b>« Также присутствуют аудио файлы »</b>'

    for i, group in enumerate(output[0]):
        if group[0] == "photo":
            if i: media.append(types.InputMediaPhoto(media=group[1]))
            else: media.append(types.InputMediaPhoto(media=group[1], caption=text))
        elif group[0] == "video":
            if i: media.append(types.InputMediaPhoto(media=group[1][3]))
            else: media.append(types.InputMediaPhoto(media=group[1][3], caption=text))
        elif group[0] == "doc":
            if group[1][2] == 4:
                if i: media.append(types.InputMediaPhoto(media=group[1][1]))
                else: media.append(types.InputMediaPhoto(media=group[1][1], caption=text))

    return text, audio, media
