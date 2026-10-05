from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import Command

from emoji import emojize

from init import *
from config import *
from vk_scripts import VkParser
from scripts import login, pars_post

router = Router()


@router.message(Command("start", "help"))
async def start(msg: Message) -> None:
    login(msg.chat.id, du, db)

    buttons = [[types.InlineKeyboardButton(text="КОМАНДЫ", callback_data="com"),
               types.InlineKeyboardButton(text="АВТОР", callback_data="auth")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons, row_width=2)

    await msg.answer(text=f'<b>Portal in VK</b> - это бот для перепоста постов со страниц в социальной сети ВКонтакте. '
                          f'Для начала работы вам нужно всего лишь вызвать команду <b>/add</b> и добавить к ней '
                          f'короткое имя личной или публичной страницы. После этого, бот начнёт присылать каждый новый '
                          f'пост с этой страницы форматируя данные с неё под сообщение в Telegram. С полным '
                          f'функционалом бота, вы можете ознакомиться по кнопке <b>КОМАНДЫ</b>\n\n'
                              
                          f'Если вы хотите ставить лайки или получать уведомления от закрытых страниц на которые '
                          f'подписаны в социальной сети, вам необходимо скинуть ссылку из поисковой строки в чат, '
                          f'после подтверждения на <a href="{loginUrl}">сайте</a>', reply_markup=keyboard)


# ИЛАЙН КЛАВИАТУРА HELP
@router.callback_query(F.data == "com")
async def function(call: CallbackQuery) -> None:
    await call.message.answer(text='<b>| КОМАНДЫ |</b>\n\n'
                                   '<b>/like</b> - лайк на пост, который вы отметили\n'
                                   '<b>/list</b> - список страниц от, которых вы получаете уведомления\n'
                                   '<b>/notif</b> - отписка или подписка от всех уведомлений\n'
                                   '<b>/last_post</b> - получение последнего поста по короткому имени страницы\n'
                                   '<b>/add</b> и <b>/del</b> - добавление и удаление странички из списка подписок\n')


@router.callback_query(F.data == "auth")
async def author(call: CallbackQuery) -> None:
    await call.message.answer(text='<b>| АВТОР |</b>\n\n<b>>></b> Этот бот не коммерческий проект, для получения '
                                   'постов из социальной сети ВКонтакте. Бот работает на сервисном токене VK API, '
                                   'пока вы не предоставите собственный. Ваш токен нужен для получения постов со '
                                   'страниц, доступ к которым есть исключительно у вас. Также это даст вам '
                                   'возможность ставить через Telegram лайки на посты в самой социальной сети!'
                                   
                                   '\n\nЯ же пишу подобные небольшие проекты, о которых вы можете узнать '
                                   'больше на моём <a href="https://github.com/IGlek">GitHub</a>.')


# КОМАНДЫ
@router.message(Command("notif"))
async def notification(msg: Message) -> None:
    user_id = login(msg.chat.id, du, db)
    status = db.get_status(user_id)

    groups = list(map(int, db.get_user_groups(user_id).split(";")))
    for group in groups: db.update_countGroup(group, -1 if status else 1)

    if status: await msg.answer("Получение постов из ВК выключено!")
    else: await msg.answer("Получение постов из ВК включено!")
    db.update_status(user_id)


@router.message(Command("add", "del"))
async def add_del(msg: Message) -> None:
    user_id = login(msg.chat.id, du, db)

    domain = msg.text.split()[-1]
    command = msg.text.split()[0]

    if "/" not in domain:
        try:
            token = db.get_token(user_id)
            if token: vk = VkParser(token)
            else: vk = VkParser(serviceToken)

            group_id, typ, last_post = vk.login(domain)

            if not du.group_exists(group_id):
                du.add_group(group_id)
            group_id = du.get_group_id(group_id)

            if not db.infoGroup_exists(group_id):
                db.add_infoGroup(group_id, typ, last_post)

            groups = db.get_user_groups(user_id)
            user_groups = groups.split(";") if groups else []

            if str(group_id) not in user_groups:
                if command == "/del":
                    await msg.answer("Вы и так не подписаны на эту группу!")
                else:
                    if db.get_countUser(user_id) < 10:
                        user_groups.append(str(group_id))
                        db.update_user_groups(user_id, ";".join(user_groups))

                        db.update_countUser(user_id, 1)
                        if db.get_status(user_id): db.update_countGroup(group_id, 1)

                        await msg.answer("Группа успешно добавлена в список уведомлений!")
                    else:
                        await msg.answer("У вас добавлено максимально количество групп!")
            else:
                if command == "/add":
                    await msg.answer("Вы уже подписаны на эту страницу!")
                else:
                    user_groups.remove(str(group_id))
                    db.update_user_groups(user_id, ";".join(user_groups))

                    db.update_countUser(user_id, -1)
                    if db.get_status(user_id): db.update_countGroup(group_id, -1)

                    await msg.answer("Группа успешно удалена из списка уведомлений!")
        except Exception as err:
            logging.info("Нет доступа к страницы:", exc_info=True)
            await msg.answer("<b>Произошла ошибка!</b> Проверьте правильность написания <b>короткого адреса</b> "
                             "страницы, <b>имеете ли вы доступ</b> к этой странице и есть ли на ней <b>хотя бы "
                             "один пост</b>!")
    else:
        if command == "/add":
            await msg.answer("Команда введена некорректно, такой страницы не существует или она закрыта для "
                             "просмотра!\n\nКорректный ввод команд: /add <i>example</i>")
        elif command == "/del":
            await msg.answer("Команда введена некорректно, такой страницы не существует или она закрыта для "
                             "просмотра!\n\nКорректный ввод команд: /del <i>example</i>")


@router.message(Command("list"))
async def lst(msg: Message) -> None:
    user_id = login(msg.chat.id, du, db)
    groups = db.get_user_groups(user_id)
    user_groups = list(map(int, groups.split(";") if groups else []))

    if user_groups:
        group_ids = [du.get_vk_id(id) for id in user_groups]

        vk = VkParser(serviceToken)
        peoples, groups = vk.info(group_ids)

        text = "<b><i>* Список страниц, от которых вы получаете уведомления!</i></b>\n"

        if peoples:
            text += "\n<b>Личные страницы пользователей</b>\n"
            for i, people in enumerate(peoples):
                text += f'{emojize(":green_circle:") if people[2] else emojize(":red_circle:")} ' \
                        f'{i + 1}. {people[1]} <a href="https://vk.com/{people[0]}">@{people[0]}</a>\n'

        if groups:
            text += "\n<b>Группы / сообщества / паблики</b>\n"
            for i, group in enumerate(groups):
                text += f'{i + 1}. {group[1]} <a href="https://vk.com/{group[0]}">@{group[0]}</a>\n'

        await msg.answer(text, disable_web_page_preview=True)
    else:
        await msg.answer("Вы <b>не добавили ни одной страницы</b> для отслеживания публикаций!")


@router.message(Command("like"))
async def like(msg: Message) -> None:
    user_id = login(msg.chat.id, du, db)
    token = db.get_token(user_id)

    if token and (msg.reply_to_message is not None):
        url = ''

        if msg.reply_to_message.entities is not None:
            for i in list(msg.reply_to_message.entities):
                i = dict(i)
                if i['type'] == 'text_link':
                    url = i['url']; break
        elif msg.reply_to_message.caption_entities is not None:
            for i in list(msg.reply_to_message.caption_entities):
                i = dict(i)
                if i['type'] == 'text_link':
                    url = i['url']; break

        if url:
            try:
                [group_id, last_post] = list(map(int, url.split('wall')[-1].split('_')))

                vk = VkParser(token)
                vk.like(group_id, last_post)

                await msg.answer('Вы поставили лайк 😉')
            except Exception as err:
                logging.error("Не удалось поставить лайк:", exc_info=True)
                await msg.answer('По <b>неизвестной причине</b> не удалось поставить лайк!')
        else:
            await msg.answer('Вы <b>ответили не на тот пост</b>, для отправки лайка!')
    else:
        await msg.answer('Вы <b>не отметили пост</b> который хотите лайкнуть или <b>не прислали свой токен</b> для '
                         'возможности лайкать посты!')


@router.message(Command("update"))
async def update(msg: Message) -> None:
    user_id = msg.chat.id
    short_id = login(msg.chat.id, du, db)

    if msg.reply_to_message is not None:
        url = ''

        if msg.reply_to_message.entities is not None:
            for i in list(msg.reply_to_message.entities):
                i = dict(i)
                if i['type'] == 'text_link':
                    url = i['url']; break
        elif msg.reply_to_message.caption_entities is not None:
            for i in list(msg.reply_to_message.caption_entities):
                i = dict(i)
                if i['type'] == 'text_link':
                    url = i['url']; break

        if url:
            try:
                [group_id, last_post] = list(map(int, url.split('wall')[-1].split('_')))

                token = db.get_token(short_id)
                if token: vk = VkParser(token)
                else: vk = VkParser(serviceToken)

                output = vk.last_post(post=f"{group_id}_{last_post}")
                text, audio, media = pars_post(types, output)

                delete_r = await bot.delete_message(chat_id=user_id, message_id=msg.reply_to_message.message_id)
                delete = await bot.delete_message(chat_id=user_id, message_id=msg.message_id)

                if audio and media:
                    post_message = await bot.send_media_group(chat_id=user_id, media=media)
                    await bot.send_media_group(chat_id=user_id, media=audio,
                                               reply_to_message_id=post_message[0].message_id)
                elif audio and media == []:
                    post_message = await bot.send_message(chat_id=user_id, text=text)
                    await bot.send_media_group(chat_id=user_id, media=audio,
                                               reply_to_message_id=post_message[0].message_id)
                elif audio == [] and media:
                    await bot.send_media_group(chat_id=user_id, media=media)
                else:
                    await bot.send_message(chat_id=user_id, text=text, disable_web_page_preview=True)

            except Exception as err:
                logging.danger("Ошибка обновления поста:", exc_info=True)
                await msg.answer(text='По неизвестной причине не удалось обновить пост!')
        else: await msg.answer(text='Вы ответили не на тот пост!')
    else: await msg.answer(text='Вы не отметили пост который хотите обновить!')


# ВЗАИМОДЕЙСТВИЕ С ДАННЫМИ ВК ПОСТОВ
@router.message(Command("last_post"))
async def last_post(msg: Message) -> None:
    user_id = msg.chat.id
    short_id = login(user_id, du, db)

    domain = msg.text.split()[-1]
    if "/" not in domain:
        try:
            token = db.get_token(short_id)
            if token: vk = VkParser(token)
            else: vk = VkParser(serviceToken)

            output = vk.last_post(domain=domain); vk.login(domain)
            text, audio, media = pars_post(types, output)

            if audio and media:
                post_message = await bot.send_media_group(chat_id=user_id, media=media)
                await bot.send_media_group(chat_id=user_id, media=audio, reply_to_message_id=post_message[0].message_id)
            elif audio and media == []:
                post_message = await bot.send_message(chat_id=user_id, text=text)
                await bot.send_media_group(chat_id=user_id, media=audio, reply_to_message_id=post_message[0].message_id)
            elif audio == [] and media:
                await bot.send_media_group(chat_id=user_id, media=media)
            else:
                await bot.send_message(chat_id=user_id, text=text, disable_web_page_preview=True)

        except Exception as err:
            logging.info("Некорректное/недоступное короткое имя:", exc_info=True)
            await msg.answer("Короткое <b>имя страницы неверное</b> или у вас <b>нет доступа</b> к этой странице!")
    else: await msg.answer("Команда введена некорректно! Корректный ввод: /last_post <b>example</b>")


# ПОЛУЧЕНИЕ ТОКЕНА ПОЛЬЗОВАТЕЛЯ
@router.message(F.content_type == ContentType.TEXT)
async def url(msg: Message) -> None:
    user_id = login(msg.chat.id, du, db)

    if checkUrl in msg.text:
        try:
            token = msg.text.split("&")[0].split("=")[-1]
            info = VkParser(token).check()

            db.update_token(user_id, token)
            await msg.answer("Токен успешно сохранён!")
        except Exception as err:
            logging.info("Некорректная ссылка:", exc_info=True)
            await msg.answer("Ваша <b>ссылка не корректна</b>, попробуйте повторить копирование!")
    else: await msg.answer("Ваше <b>сообщение не корректно</b>, необходима ссылка, что отобразилась в строке "
                           "поиске после подтверждения доступа!")
