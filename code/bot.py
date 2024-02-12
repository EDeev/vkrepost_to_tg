import logging, config, asyncio, time, sql, random

from aiogram import Bot, Dispatcher, executor, types
from emoji import emojize

from vk_scripts import VkParser
from scripts import login, pars_post

# log level
logging.basicConfig(level=logging.INFO)

# bot init
bot = Bot(token=config.botToken)
dp = Dispatcher(bot)

# connection db
du = sql.Users('../db/users.db')
db = sql.Base('../db/base.db')


# events
@dp.message_handler(commands=["start", "help"])
async def start(message: types.Message):
    login(message.chat.id, du, db)

    buttons = [types.InlineKeyboardButton(text="КОМАНДЫ", callback_data="com"),
               types.InlineKeyboardButton(text="АВТОР", callback_data="auth")]

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)

    await message.answer(text=f'*Portal in VK* - это бот для перепоста постов со страниц в социальной сети ВКонтакте. '
                              f'Для начала работы вам нужно всего лишь вызвать команду */add* и добавить к ней короткое '
                              f'имя личной или публичной страницы. После этого, бот начнёт присылать каждый новый пост '
                              f'с этой страницы форматируя данные с неё под сообщение в Telegram. С полным функционалом '
                              f'бота, вы можете ознакомиться по кнопке *КОМАНДЫ*\n\n'
                              
                              f'Если вы хотите ставить лайки или получать уведомления от закрытых страниц на которые '
                              f'подписаны в социальной сети, вам необходимо скинуть ссылку из поисковой строки в чат, '
                              f'после подтверждения на [сайте]({config.loginUrl})',
                         parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)


# ИЛАЙН КЛАВИАТУРА HELP
@dp.callback_query_handler(text="com")
async def function(call: types.CallbackQuery):
    await call.message.answer(text='*| КОМАНДЫ |*\n\n'
                                   f'*/like* - лайк на пост, который вы отметили\n'
                                   f'*/list* - список страниц от, которых вы получаете уведомления\n'
                                   f'*/notif* - отписка или подписка от всех уведомлений\n'
                                   f'*/last_post* - получение последнего поста по короткому имени страницы\n'
                                   f'*/add* и */del* - добавление и удаление странички из списка подписок\n',
                              parse_mode=types.ParseMode.MARKDOWN)


@dp.callback_query_handler(text="auth")
async def author(call: types.CallbackQuery):
    await call.message.answer(text='*| АВТОР |*\n\n*>>* Этот бот не коммерческий проект, для получения постов из '
                                   'социальной сети ВКонтакте. Бот работает на сервисном токене VK API, пока вы не '
                                   'предоставите собственный. Ваш токен нужен для получения постов со страниц, '
                                   'доступ к которым есть исключительно у вас. Также это даст вам возможность ставить '
                                   'через Telegram лайки на посты в самой социальной сети!'
                                   
                                   '\n\nЯ же пишу подобные небольшие проекты, о которых вы можете узнать '
                                   'больше на моём [GitHub](https://github.com/IGlek).',
                              parse_mode=types.ParseMode.MARKDOWN)


# КОМАНДЫ
@dp.message_handler(commands=["notif"])
async def notification(message: types.Message):
    user_id = login(message.chat.id, du, db)
    status = db.get_status(user_id)

    groups = list(map(int, db.get_user_groups(user_id).split(";")))
    for group in groups: db.update_countGroup(group, -1 if status else 1)

    if status: await message.answer("Получение постов из ВК выключено!")
    else: await message.answer("Получение постов из ВК включено!")
    db.update_status(user_id)


@dp.message_handler(commands=["add", "del"])
async def add_del(message: types.Message):
    user_id = login(message.chat.id, du, db)
    domain = message.get_args()

    if domain:
        try:
            token = db.get_token(user_id)
            if token: vk = VkParser(token)
            else: vk = VkParser(config.serviceToken)

            group_id, typ, last_post = vk.login(domain)

            if not du.group_exists(group_id):
                du.add_group(group_id)
            group_id = du.get_group_id(group_id)

            if not db.infoGroup_exists(group_id):
                db.add_infoGroup(group_id, typ, last_post)

            groups = db.get_user_groups(user_id)
            user_groups = groups.split(";") if groups else []

            if str(group_id) not in user_groups:
                if message.get_command() == "/del":
                    await message.answer("Вы и так не подписаны на эту группу!")
                else:
                    if db.get_countUser(user_id) < 10:
                        user_groups.append(str(group_id))
                        db.update_user_groups(user_id, ";".join(user_groups))

                        db.update_countUser(user_id, 1)
                        if db.get_status(user_id): db.update_countGroup(group_id, 1)

                        await message.answer("Группа успешно добавлена в список уведомлений!")
                    else:
                        await message.answer("У вас добавлено максимально количество групп!")
            else:
                if message.get_command() == "/add":
                    await message.answer("Вы уже подписаны на эту страницу!")
                else:
                    user_groups.remove(str(group_id))
                    db.update_user_groups(user_id, ";".join(user_groups))

                    db.update_countUser(user_id, -1)
                    if db.get_status(user_id): db.update_countGroup(group_id, -1)

                    await message.answer("Группа успешно удалена из списка уведомлений!")
        except Exception as e:
            await message.answer("Произошла ошибка! Проверьте правильность написания короткого адреса страницы "
                                 "и имеете ли вы доступ к этой странице!")
    else:
        if message.get_command() == "/add":
            await message.answer("Команда введена некорректно, такой страницы не существует или она закрыта для "
                                 "просмотра!\n\nКорректный ввод команд: /add <i>example</i>", types.ParseMode.HTML)
        elif message.get_command() == "/del":
            await message.answer("Команда введена некорректно, такой страницы не существует или она закрыта для "
                                 "просмотра!\n\nКорректный ввод команд: /del <i>example</i>", types.ParseMode.HTML)


@dp.message_handler(commands=["list"])
async def lst(message: types.Message):
    user_id = login(message.chat.id, du, db)
    groups = db.get_user_groups(user_id)
    user_groups = list(map(int, groups.split(";") if groups else []))

    if user_groups:
        group_ids = [du.get_vk_id(id) for id in user_groups]

        vk = VkParser(config.serviceToken)
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

        await message.answer(text, types.ParseMode.HTML)
    else:
        await message.answer("Вы не добавили ни одной страницы для отслеживания публикаций!")


@dp.message_handler(commands=["like"])
async def like(message: types.Message):
    user_id = login(message.chat.id, du, db)
    token = db.get_token(user_id)

    if token and 'reply_to_message' in message:
        url = ''

        if 'entities' in message.reply_to_message:
            for i in message.reply_to_message.entities:
                if i['type'] == 'text_link': url = i['url']; break
        elif 'caption_entities' in message.reply_to_message:
            for i in message.reply_to_message.caption_entities:
                if i['type'] == 'text_link': url = i['url']; break

        if url:
            try:
                [group_id, last_post] = list(map(int, url.split('wall')[-1].split('_')))

                vk = VkParser(token)
                vk.like(group_id, last_post)

                await message.answer(text='Вы поставили лайк 😉')
            except Exception as e:
                await message.answer(text='По неизвестной причине не удалось поставить лайк!')
        else:
            await message.answer(text='Вы ответили не на тот пост, для отправки лайка!')
    else:
        await message.answer(text='Вы не отметили пост который хотите лайкнуть или не прислали свой токен для '
                                  'возможности лайкать посты!')


# ВЗАИМОДЕЙСТВИЕ С ДАННЫМИ ВК ПОСТОВ
@dp.message_handler(commands=["last_post"])
async def last_post(message: types.Message):
    user_id = message.chat.id
    short_id = login(user_id, du, db)
    domain = message.get_args()

    if domain:
        try:
            token = db.get_token(short_id)
            if token: vk = VkParser(token)
            else: vk = VkParser(config.serviceToken)

            output = vk.last_post(domain=domain); vk.login(domain)
            text, audio, media = pars_post(types, output)

            if audio and media:
                post_message = await bot.send_media_group(chat_id=user_id, media=media)
                await bot.send_media_group(chat_id=user_id, media=audio, reply_to_message_id=post_message[0].message_id)
            elif audio and media == []:
                post_message = await bot.send_message(chat_id=user_id, text=text, parse_mode=types.ParseMode.MARKDOWN)
                await bot.send_media_group(chat_id=user_id, media=audio, reply_to_message_id=(post_message[0].message_id))
            elif audio == [] and media:
                await bot.send_media_group(chat_id=user_id, media=media)
            else:
                await bot.send_message(chat_id=user_id, text=text, parse_mode=types.ParseMode.MARKDOWN)

        except Exception as e:
            await message.answer("Короткое имя страницы неверное или у вас нет доступа к этой странице!")
    else:
        await message.answer("Команда введена некорректно! Корректный ввод: /last_post example")


# ПОЛУЧЕНИЕ ТОКЕНА ПОЛЬЗОВАТЕЛЯ
@dp.message_handler(content_types="text")
async def url(message: types.Message):
    user_id = login(message.chat.id, du, db)

    if config.checkUrl in message.text:
        try:
            token = message.text.split("&")[0].split("=")[-1]
            info = VkParser(token).check()

            db.update_token(user_id, token)
            await message.answer("Токен успешно сохранён!")
        except Exception as e:
            await message.answer("Ваша ссылка не корректна, попробуйте повторить копирование!")
    else:
        await message.answer("Ваше сообщение не корректно, необходима ссылка, что отобразилась в строке поиске после"
                             " подтверждения доступа!")


# ПРОВЕРКА СТРАНИЦ НА НОВЫЕ ПОСТЫ
async def timer(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        notif_group = list(map(lambda x: x[0], db.all_notifGroup()))
        activ_user = list(map(lambda x: [x[0], list(map(int, x[1].split(';')))], db.all_activUser()))
        sub_user = list(map(lambda x: [x[0], list(map(int, x[1].split(';')))], db.all_subUser()))

        for group_id in notif_group:
            time.sleep(1)

            tokens = [x[0] for x in activ_user if group_id in x[1]]
            users = [x[0] for x in sub_user if group_id in x[1]]

            if tokens:
                user_id = tokens[random.randrange(len(tokens))]
                vk = VkParser(db.get_token(user_id))
            else: vk = VkParser(config.serviceToken)

            try:
                output = vk.last_post(owner_id=du.get_vk_id(group_id))
                last_post = db.get_postGroup(group_id)

                if output[3] > last_post:
                    text, audio, media = pars_post(types, output)
                    db.update_postGroup(group_id, output[3])

                    for sub in users:
                        tg_id = du.get_tg_id(sub)

                        if audio and media:
                            post_message = await bot.send_media_group(chat_id=tg_id, media=media)
                            await bot.send_media_group(chat_id=tg_id, media=audio, reply_to_message_id=post_message[0].message_id)
                        elif audio and media == []:
                            post_message = await bot.send_message(chat_id=tg_id, text=text, parse_mode=types.ParseMode.MARKDOWN)
                            await bot.send_media_group(chat_id=tg_id, media=audio, reply_to_message_id=post_message[0].message_id)
                        elif audio == [] and media:
                            await bot.send_media_group(chat_id=tg_id, media=media)
                        else:
                            await bot.send_message(chat_id=tg_id, text=text, parse_mode=types.ParseMode.MARKDOWN)

            except Exception as e:
                print(repr(e))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(timer(60))  # ПРОВЕРКА КАЖДУЮ МИНУТУ
    executor.start_polling(dp, skip_updates=True)
