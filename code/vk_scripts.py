from html import escape

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

    def last_post(self, owner_id=None, domain=None, post=None):
        if post: wall = self.vk.wall.getById(posts=post, extended=1)
        else: wall = self.vk.wall.get(owner_id=owner_id, domain=domain, count=2, extended=1)

        post = max([[int(pt["id"]), pt] for pt in wall["items"]])
        owner_id = post[1]['owner_id']

        if owner_id > 0:
            [name, domain] = [[per['first_name'] + ' ' + per['last_name'], per['screen_name']] for per in wall["profiles"] if per["id"] == owner_id][0]
        else:
            [name, domain] = [[gro['name'], gro['screen_name']] for gro in wall["groups"] if gro["id"] == int(str(owner_id)[1:])][0]

        if 'copy_history' in post[1]:
            comment, orig_id = post[1]['text'], post[0]

            post = [post[1]['copy_history'][0]['id'], post[1]['copy_history'][0]]
            owner_id_r = post[1]['owner_id']

            if owner_id_r > 0:
                [name_r, domain_r] = [[per['first_name'] + ' ' + per['last_name'], per['screen_name']] for per in wall["profiles"] if per["id"] == owner_id_r][0]
            else:
                [name_r, domain_r] = [[gro['name'], gro['screen_name']] for gro in wall["groups"] if gro["id"] == int(str(owner_id_r)[1:])][0]

            return get_output(post, name_r, domain_r, [orig_id, owner_id, name, domain, comment])
        else:
            return get_output(post, name, domain)


def get_output(post, name, domain, repost=None):
    [post_id, post] = post
    owner_id, output = post['owner_id'], []

    attachments = post.get('attachments', [])
    types = [[typ['type'], typ] for typ in attachments]

    for typ in types:
        if typ[0] == 'photo':
            output.append([typ[0], typ[1]['photo']['sizes'][-1]['url']])
        elif typ[0] == 'video':
            video = typ[1]['video']
            # обложка: самая крупная из доступных
            frame = video.get('photo_1280') or video.get('photo_800') or video.get('photo_320')
            if frame is None and video.get('image'):
                frame = video['image'][-1]['url']

            output.append([typ[0], [video['title'], video.get('duration', 0), video.get('views', 0), frame]])
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

    if repost:
        [author_id, author_owner_id, author_name, author_domain, author_comment] = repost

        comment = f"<b>Автор репоста -</b> <a href='https://vk.com/{author_domain}?w=wall{author_owner_id}_{author_id}'>{escape(author_name)}</a>"
        if author_comment != "": comment += f"\n<blockquote>{escape(author_comment)}</blockquote>\n"
        comment += f"\n<b>Автор поста -</b> <a href='https://vk.com/{domain}?w=wall{owner_id}_{post_id}'>{escape(name)}</a>"

        return [output, f"{post['text']}", comment, author_id]
    else:
        return [output, f"{post['text']}",
                f"<b>Автор поста -</b> <a href='https://vk.com/{domain}?w=wall{owner_id}_{post_id}'>{escape(name)}</a>", post_id]