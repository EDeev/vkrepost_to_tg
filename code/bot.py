import asyncio
import logging
import random

import scripts
import vk_scripts
from init import bot, dp, du, db
from config import serviceToken
from handlers import router


async def check_group(group_id, activ_user, sub_user):
    tokens = [x[0] for x in activ_user if group_id in x[1]]
    users = [x[0] for x in sub_user if group_id in x[1]]

    # токен случайного подписчика даёт доступ к закрытым страницам, иначе — сервисный ключ
    if tokens:
        vk = vk_scripts.VkParser(db.get_token(random.choice(tokens)))
    else: vk = vk_scripts.VkParser(serviceToken)

    # vk_api синхронный — в отдельном потоке, чтобы не замирал весь бот
    output = await asyncio.to_thread(vk.last_post, owner_id=du.get_vk_id(group_id))
    last_post = db.get_postGroup(group_id)

    if output[3] > last_post:
        text, audio, media = scripts.pars_post(output)
        db.update_postGroup(group_id, output[3])

        for sub in users:
            try:
                await scripts.send_post(bot, du.get_tg_id(sub), text, audio, media)
            except Exception:
                # подписчик мог заблокировать бота — остальным пост всё равно уходит
                logging.warning("Не удалось отправить пост подписчику %s", sub, exc_info=True)


async def timer(wait_for) -> None:
    while True:
        await asyncio.sleep(wait_for)

        notif_group = [x[0] for x in db.all_notifGroup()]
        activ_user = [[x[0], list(map(int, x[1].split(';')))] for x in db.all_activUser() if x[1]]
        sub_user = [[x[0], list(map(int, x[1].split(';')))] for x in db.all_subUser() if x[1]]

        for group_id in notif_group:
            await asyncio.sleep(1)  # пауза между страницами — лимиты VK API

            try:
                await check_group(group_id, activ_user, sub_user)
            except Exception:
                logging.error("Ошибка обновления поста:", exc_info=True)


async def main() -> None:
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def process() -> None:
    await asyncio.gather(main(), timer(60))


if __name__ == "__main__":
    try: asyncio.run(process())
    except KeyboardInterrupt: pass
