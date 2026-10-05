import os

# TOKENS
botToken = os.getenv("BOT_TOKEN", "XXXXXXXXXXXXXXXXXXXXXXXX")  # @vkportalbot
serviceToken = os.getenv("VK_SERVICE_TOKEN", "")  # сервисный ключ приложения VK

# URL
loginUrl = os.getenv("VK_LOGIN_URL", "https://oauth.vk.com/authorize?client_id=6121396&scope=215985366"
                                     "&redirect_uri=https://oauth.vk.com/blank.html&display=page"
                                     "&response_type=token&revoke=1")
checkUrl = "https://oauth.vk.com/blank.html#access_token="

# VARIABILITY
unvote = {True: 'без возможности переголосовать', False: 'с возможностью переголосовать'}
anonymous = {True: 'анонимный опрос', False: 'не анонимный опрос'}

# DATA
data = {0: 'Б', 1: 'КБ', 2: 'МБ', 3: 'ГБ', 4: 'ТБ'}
dura = {0: 'с.', 1: 'мин.'}
