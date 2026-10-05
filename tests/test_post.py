import asyncio
from types import SimpleNamespace

import scripts
import vk_scripts


def wall(text, attachments, repost=None):
    post = {"id": 7, "owner_id": -100, "text": text, "attachments": attachments}
    if repost:
        post["copy_history"] = [repost]
    return {"items": [post], "groups": [{"id": 100, "name": "Паблик <&>", "screen_name": "pub"}],
            "profiles": [{"id": 5, "first_name": "Иван", "last_name": "Петров", "screen_name": "ivan"}]}


def parse(response):
    class Api:
        class wall:
            @staticmethod
            def get(**_): return response
    parser = vk_scripts.VkParser.__new__(vk_scripts.VkParser)
    parser.vk = Api
    return parser.last_post(owner_id=-100)


def photo(url):
    return {"type": "photo", "photo": {"sizes": [{"url": url + "-small"}, {"url": url}]}}


def test_text_is_escaped_and_mentions_become_links():
    out = parse(wall("1 < 2 & [id5|Иван] пишет <b>", []))
    text, audio, media = scripts.pars_post(out)
    assert "1 &lt; 2 &amp; <a href='https://vk.com/id5'>Иван</a> пишет &lt;b&gt;" in text
    assert "Паблик &lt;&amp;&gt;" in text
    assert audio == [] and media == []


def test_attachments_links_are_html_and_media_limited():
    atts = [{"type": "link", "link": {"title": "Сайт", "url": "https://example.com/?a=1&b=2"}}]
    atts += [photo(f"https://img/{i}") for i in range(12)]
    text, audio, media = scripts.pars_post(parse(wall("пост", atts)))
    assert "<a href='https://example.com/?a=1&amp;b=2'>Сайт</a>" in text
    assert "](" not in text  # раньше ссылки оформлялись Markdown-синтаксисом
    assert len(media) == 10 and media[0].media == "https://img/0"


def test_repost_has_both_authors():
    orig = {"id": 3, "owner_id": 5, "text": "оригинал", "attachments": []}
    text, _, _ = scripts.pars_post(parse(wall("мой комментарий", [], repost=orig)))
    assert "Автор репоста" in text and "Иван Петров" in text and "<blockquote>мой комментарий</blockquote>" in text


def test_split_text_keeps_lines():
    text = "\n".join(f"<b>строка {i}</b>" for i in range(1000))
    parts = scripts.split_text(text, 4096)
    assert all(len(p) <= 4096 for p in parts)
    assert "".join(parts).count("<b>") == 1000 and all(p.count("<b>") == p.count("</b>") for p in parts)


class FakeBot:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        async def method(**kwargs):
            self.calls.append((name, kwargs))
            msg = SimpleNamespace(message_id=len(self.calls))
            return [msg] if name == "send_media_group" else msg
        return method


def send(text, audio, media):
    bot = FakeBot()
    asyncio.run(scripts.send_post(bot, 1, text, audio, media))
    return bot.calls


def test_single_photo_is_sent_as_photo_not_album():
    _, _, media = scripts.pars_post(parse(wall("пост", [photo("https://img/1")])))
    calls = send("короткий текст", [], media)
    assert [c[0] for c in calls] == ["send_photo"] and calls[0][1]["caption"] == "короткий текст"


def test_long_text_with_album_goes_as_separate_messages():
    _, _, media = scripts.pars_post(parse(wall("пост", [photo("a"), photo("b")])))
    calls = send("x" * 3000, [], media)
    assert calls[0][0] == "send_media_group" and calls[0][1]["media"][0].caption is None
    assert calls[1][0] == "send_message" and calls[1][1]["reply_to_message_id"] == 1


def test_text_with_single_audio():
    atts = [{"type": "audio", "audio": {"title": "Песня", "url": "https://a/1.mp3", "artist": "Автор"}}]
    text, audio, media = scripts.pars_post(parse(wall("пост", atts)))
    calls = send(text, audio, media)
    assert [c[0] for c in calls] == ["send_message", "send_audio"]
    assert calls[1][1]["reply_to_message_id"] == 1
