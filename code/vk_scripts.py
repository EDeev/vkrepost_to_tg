import vk_api


class VkParser:
    def __init__(self, token):
        """Подключаемся к API VK"""
        self.session = vk_api.VkApi(token=token)
        self.vk = self.session.get_api()

    def check(self):
        return self.vk.account.getInfo(fields="lang")

    def like(self, owner_id, post_id):
        return self.vk.likes.add(type="post", owner_id=owner_id, item_id=post_id)

    def login(self, domain):
        posts = self.vk.wall.get(domain=domain, count=3)
        post = max([[int(pt["id"]), int(pt["owner_id"])] for pt in posts["items"]])

        [last_post, group_id] = post
        typ = 0 if group_id > 0 else 1
        return group_id, typ, last_post

    def info(self, group_ids):
        groups, peoples = [], []

        for id in group_ids:
            if id > 0: peoples.append(id)
            else: groups.append(id)

        if groups:
            data = self.vk.groups.getById(group_ids=", ".join(list(map(lambda x: str(x)[1:], groups))))
            groups = [[elem['screen_name'], elem['name']] for elem in data]

        if peoples:
            data = self.vk.users.get(user_ids=", ".join(list(map(str, peoples))), fields="domain, online")
            peoples = [[elem['domain'], elem['first_name'] + ' ' + elem['last_name'], elem['online']] for elem in data]

        return peoples, groups

    def last_post(self, owner_id=None, domain=None):
        wall = self.vk.wall.get(owner_id=owner_id, domain=domain, count=2, extended=1)
        post = max([[int(pt["id"]), pt] for pt in wall["items"]])

        [post_id, post] = post
        owner_id, output = post['owner_id'], []

        if owner_id > 0: [name, domain] = [[per['first_name'] + ' ' + per['last_name'], per['screen_name']]
                                           for per in wall["profiles"] if per["id"] == owner_id][0]
        else: [name, domain] = [[gro['name'], gro['screen_name']]
                                for gro in wall["groups"] if gro["id"] == int(str(owner_id)[1:])][0]

        attachments = post['attachments']
        types = [[typ['type'], typ] for typ in attachments]

        for typ in types:
            if typ[0] == 'photo':
                output.append([typ[0], typ[1]['photo']['sizes'][-1]['url']])
            elif typ[0] == 'video':
                output.append([typ[0], typ[1]['video']['title']])
            elif typ[0] == "doc":
                output.append([typ[0], [typ[1]['doc']['title'], typ[1]['doc']['url'],
                                        typ[1]['doc']['type'], typ[1]['doc']['size']]])
            elif typ[0] == "audio":
                output.append([typ[0], [typ[1]['audio']['title'], typ[1]['audio']['url'], typ[1]['audio']['artist']]])
            elif typ[0] == "poll":
                answer = [[que['text'], que['votes']] for que in typ[1]['poll']['answers']]
                output.append([typ[0], [typ[1]['poll']['question'], typ[1]['poll']['votes'],
                                        typ[1]['poll']['disable_unvote'], typ[1]['poll']['anonymous'], answer]])
            elif typ[0] == "link":
                output.append([typ[0], [typ[1]['link']['title'], typ[1]['link']['url']]])

        return [output, post['text'],
                f"*Автор поста -* [{name}](https://vk.com/{domain}?w=wall{owner_id}_{post_id})", post_id]


