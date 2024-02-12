import sqlite3


class Users:
    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    # КОМАНДЫ USER
    def user_exists(self, user_id):
        """Проверяем, есть ли уже пользователь в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `user` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id):
        """Добавляем нового пользователя"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `user` (`user_id`) VALUES(?)", (user_id,))

    def get_user_id(self, user_id):
        """Получаем короткое айди юзера"""
        with self.connection:
            return self.cursor.execute('SELECT `id` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]

    def get_tg_id(self, user_id):
        """Получаем длинное айди юзера"""
        with self.connection:
            return self.cursor.execute('SELECT `user_id` FROM `user` WHERE `id` = ?', (user_id,)).fetchone()[0]

    # КОМАНДЫ GROUP
    def group_exists(self, group_id):
        """Проверяем, есть ли уже группа в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `group` WHERE `group_id` = ?', (group_id,)).fetchall()
            return bool(len(result))

    def add_group(self, group_id):
        """Добавляем новую группу"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `group` (`group_id`) VALUES(?)", (group_id,))

    def get_group_id(self, group_id):
        """Получаем короткое айди группы"""
        with self.connection:
            return self.cursor.execute('SELECT `id` FROM `group` WHERE `group_id` = ?', (group_id,)).fetchone()[0]

    def get_vk_id(self, group_id):
        """Получаем длинное айди группы"""
        with self.connection:
            return self.cursor.execute('SELECT `group_id` FROM `group` WHERE `id` = ?', (group_id,)).fetchone()[0]

    # ЗАКРЫТИЕ ВЫЗОВА
    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()


class Base:
    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    # КОМАНДЫ USER
    def infoUser_exists(self, user_id):
        """Проверяем, есть ли данные уже в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `user` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_infoUser(self, user_id):
        """Добавляем информацию о пользователе"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `user` (`user_id`) VALUES(?)", (user_id, ))

    def all_activUser(self):
        """Список активных пользователей"""
        with self.connection:
            return self.cursor.execute('SELECT `user_id`, `groups` FROM `user` WHERE `status` = 1 AND `count` > 0 '
                                       'AND `token` NOT NULL').fetchall()

    def all_subUser(self):
        """Список пользователей подписанных на группу"""
        with self.connection:
            return self.cursor.execute('SELECT `user_id`, `groups` FROM `user` WHERE `status` = 1 AND `count` > 0').fetchall()

    def get_status(self, user_id):
        """Получаем статус рассылки уведомлений"""
        with self.connection:
            return self.cursor.execute('SELECT `status` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]

    def update_status(self, user_id):
        """Обновляем статус рассылки уведомлений"""
        with self.connection:
            status = self.cursor.execute('SELECT `status` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]
            return self.cursor.execute("UPDATE `user` SET `status` = ? WHERE `user_id` = ?", (not status, user_id))

    def get_user_groups(self, user_id):
        """Получаем группы на которые подписан пользователь"""
        with self.connection:
            return self.cursor.execute('SELECT `groups` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]

    def update_user_groups(self, user_id, groups):
        """Обновляем группы на которые подписан пользователь"""
        with self.connection:
            return self.cursor.execute("UPDATE `user` SET `groups` = ? WHERE `user_id` = ?", (groups, user_id))

    def get_token(self, user_id):
        """Получаем access token пользователя"""
        with self.connection:
            return self.cursor.execute('SELECT `token` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]

    def update_token(self, user_id, token):
        """Обновляем access token пользователя"""
        with self.connection:
            return self.cursor.execute("UPDATE `user` SET `token` = ? WHERE `user_id` = ?", (token, user_id))

    def get_countUser(self, user_id):
        """Получаем количество подписок пользователя"""
        with self.connection:
            return self.cursor.execute('SELECT `count` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]

    def update_countUser(self, user_id, num):
        """Обновляем количество подписок пользователя"""
        with self.connection:
            count = self.cursor.execute('SELECT `count` FROM `user` WHERE `user_id` = ?', (user_id,)).fetchone()[0]
            return self.cursor.execute("UPDATE `user` SET `count` = ? WHERE `user_id` = ?", (count + num, user_id))

    # КОМАНДЫ GROUP
    def infoGroup_exists(self, group_id):
        """Проверяем, есть ли данные уже в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `group` WHERE `group_id` = ?', (group_id,)).fetchall()
            return bool(len(result))

    def add_infoGroup(self, group_id, tp, last_post):
        """Добавляем информацию о группе"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `group` (`group_id`, `type`, `last_post`) VALUES(?, ?, ?)",
                                       (group_id, tp, last_post))

    def all_notifGroup(self):
        """Список отслеживаемых групп"""
        with self.connection:
            return self.cursor.execute('SELECT `group_id` FROM `group` WHERE `count` > 0').fetchall()

    def get_postGroup(self, group_id):
        """Получаем номер последнего поста"""
        with self.connection:
            return self.cursor.execute('SELECT `last_post` FROM `group` WHERE `group_id` = ?', (group_id,)).fetchone()[0]

    def update_postGroup(self, group_id, last_post):
        """Обновляем номер последнего поста"""
        with self.connection:
            return self.cursor.execute("UPDATE `group` SET `last_post` = ? WHERE `group_id` = ?", (last_post, group_id))

    def update_countGroup(self, group_id, num):
        """Обновляем количество подписок на группу"""
        with self.connection:
            count = self.cursor.execute('SELECT `count` FROM `group` WHERE `group_id` = ?', (group_id,)).fetchone()[0]
            return self.cursor.execute("UPDATE `group` SET `count` = ? WHERE `group_id` = ?", (count + num, group_id))

    # ЗАКРЫТИЕ ВЫЗОВА
    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
