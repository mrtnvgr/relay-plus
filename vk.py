import requests

import threading
import time


class Vk:
    def __init__(self, config):
        self.config = config
        self.token = self.config["vk"]["token"]

    def method(self, method, params):
        """VkApi Method Wrapper"""
        session = requests.Session()
        params["access_token"] = self.token
        params["v"] = "5.131"
        response = session.get(
            f"https://api.vk.com/method/{method}", params=params
        ).json()
        if "error" in response:
            error = response["error"]
            if error["error_code"] != 5:  # 5 - auth failed
                print(error["error_msg"])
            return error["error_code"]
        else:
            return response["response"]


class VkListener(threading.Thread):
    def __init__(self, master):
        super().__init__()
        self.master = master

        # Get group info
        self.domain = "doujinmusic"
        group_info = self.master.vk.method("groups.getById", {"group_id": self.domain})[
            0
        ]
        self.domain_id = f'-{group_info["id"]}'

    def run(self):
        """VkListener thread main loop"""
        while True:
            self.checkPosts()
            time.sleep(self.master.config.config["vk"]["timeout"])

    def checkPosts(self):
        """Vk new post checker"""

        vk = self.master.config.config["vk"]

        # Get wall posts
        count = vk["maxHistory"]
        payload = {"domain": self.domain, "offset": 1, "count": count}
        posts = self.master.vk.method("wall.get", payload)

        # Check for errors
        if type(posts) is int:

            # Check if vk token is right
            if posts == 5:
                print("Invalid vk token.")
                exit(1)

            # Skip unknown internal server errors
            elif posts == 10:
                return

            else:
                self.master.tg.sendMessage(f"Unknown error: {posts}")
                return

        posts = posts["items"]

        if vk["post_types"]["donut"]:

            # Check if user has donut access
            payload = {"owner_id": self.domain_id}
            isDon = self.master.vk.method("donut.isDon", payload)

            if isDon == 1:
                # Get donut posts

                payload = {
                    "domain": self.domain,
                    "offset": 1,
                    "count": count,
                    "filter": "donut",
                }
                donut_posts = self.master.vk.method("wall.get", payload)

                # Merge lists
                posts = posts + donut_posts["items"]

                # Sort and strip posts
                posts = sorted(posts, key=lambda d: d["id"], reverse=True)[:count]

        # Iterate through posts
        for post in posts:

            # Check if post id in history

            history = vk["history"]
            if post["id"] not in history:

                # Check post type
                whitelist = False
                whitetags = vk["whitelist"]

                blacklist = False
                blacktags = vk["blacklist"]

                # Iterate through list tags and check
                for tag in whitetags:
                    if tag in post["text"]:
                        whitelist = True

                for tag in blacktags:
                    if tag in post["text"]:
                        blacklist = True

                # Get post type bools
                types = vk["post_types"]

                albums = (
                    (whitelist and not blacklist)
                    and "@doujinmusic" in post["text"]
                    and types["albums"]
                )

                articles = "#статьи@doujinmusic" in post["text"] and types["articles"]

                offtopic = "@doujinmusic" not in post["text"] and types["offtopic"]

                donut = post["donut"]["is_donut"] and types["donut"]

                if donut:

                    post["text"] = "<b>VK DONUT POST</b>\n" + post["text"]

                if albums or articles or offtopic or donut:
                    # Add post to history
                    self.master.config.addHistory(post["id"])

                    self.master.log.info(f"VK post: {post['id']}")

                    self.preparePost(post)

    def preparePost(self, post):
        # Add link to the post
        post_url = f"vk.com/wall{post['from_id']}_{post['id']}"
        post["text"] += f" <a href='{post_url}'>(link)</a>"

        # Parse attachments
        if "attachments" in post:

            # Parse doc attachments
            for attachment in post["attachments"][:]:

                # Check if attachment type is document
                if attachment["type"] == "doc":

                    doc = attachment["doc"]

                    # Get document data
                    url = doc["url"]
                    title = doc["title"]

                    # Add link to post text
                    post["text"] += f"\n\n<a href='{url}'>{title}</a>"

                    # Remove document from attachments
                    post["attachments"].remove(attachment)

            # Iterate through attachments
            for attachment in post["attachments"]:

                # Reset variables
                payload = {}
                method = "sendMessage"

                # Upload photos
                if attachment["type"] == "photo":

                    # Set photo key
                    photo_url = attachment["photo"]["sizes"][-1]["url"]
                    payload["photo"] = photo_url

                    # Change send method type
                    method = "sendPhoto"

                    # Set caption key
                    payload["caption"] = post["text"]

                # Upload links
                elif attachment["type"] == "link":

                    link = attachment["link"]

                    # Check if link is playlist
                    if "description" in link:
                        if link["description"] == "Плейлист":

                            # Parse playlist url
                            playlist_url = link["url"].split("_")
                            owner_id = playlist_url[1].split("playlist")[1]
                            album_id = playlist_url[2].split("&")[0]

                            payload = {
                                "owner_id": owner_id,
                                "album_id": album_id,
                            }
                            # Get audios from playlist
                            audios = self.master.vk.method("audio.get", payload)

                            # Iterate through audios
                            if type(audios) is not int and "items" in audios:

                                media = []

                                for audio in audios["items"]:

                                    # Add audio to list
                                    # FIXME: If audio is url -> performer, title, thumb tags does not work
                                    # NOTE: This is a telegram issue, impossible to fix.
                                    media.append(
                                        {
                                            "type": "audio",
                                            "media": audio["url"],
                                            "duration": audio["duration"],
                                            "performer": audio["artist"],
                                            "title": audio["title"],
                                            "caption": f"{audio['artist']} \u2014 {audio['title']}",
                                        }
                                    )

                                    self.master.log.info(
                                        f"         Music: {audio['title']}"
                                    )

                                    # Send media group and clear media list
                                    if len(media) == 10:
                                        self.master.tg.sendMediaGroup(media)
                                        media.clear()

                                # Send media group
                                self.master.tg.sendMediaGroup(media)

                            continue

                else:
                    print(attachment["type"])
                    continue

                payload["text"] = post["text"]

                # Send telegram message
                response = self.master.tg.method(method, payload)
                if "error_code" in response:
                    self.master.log.error(f'{method}: {response["description"]}')

        else:

            # Send telegram message
            self.master.tg.method("sendMessage", {"text": post["text"]})
