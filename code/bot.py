import asyncio, logging, time, random, scripts, vk_scripts

from init import *
from config import *
from handlers import router


async def timer(wait_for) -> None:
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
                vk = vk_scripts.VkParser(db.get_token(user_id))
            else: vk = vk_scripts.VkParser(serviceToken)

            try:
                output = vk.last_post(owner_id=du.get_vk_id(group_id))
                last_post = db.get_postGroup(group_id)

                if output[3] > last_post:
                    text, audio, media = scripts.pars_post(types, output)
                    db.update_postGroup(group_id, output[3])

                    for sub in users:
                        tg_id = du.get_tg_id(sub)

                        if audio and media:
                            post_message = await bot.send_media_group(chat_id=tg_id, media=media)
                            await bot.send_media_group(chat_id=tg_id, media=audio,
                                                       reply_to_message_id=post_message[0].message_id)
                        elif audio and media == []:
                            post_message = await bot.send_message(chat_id=tg_id, text=text)
                            await bot.send_media_group(chat_id=tg_id, media=audio,
                                                       reply_to_message_id=post_message[0].message_id)
                        elif audio == [] and media:
                            await bot.send_media_group(chat_id=tg_id, media=media)
                        else:
                            await bot.send_message(chat_id=tg_id, text=text, disable_web_page_preview=True)

            except Exception as err:
                logging.error("Ошибка обновления поста:", exc_info=True)


async def main() -> None:
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), skipUpdates=True)


async def process() -> None:
    await asyncio.gather(main(), timer(60))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try: asyncio.run(process())
    except KeyboardInterrupt: pass
