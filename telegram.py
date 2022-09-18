import requests
import json

class TelegramAPI:
    def __init__(self, config):
        self.config = config["telegram"]

    def method(self, method, payload, **kwargs):
        payload["chat_id"] = self.config["user_id"]
        token = self.config["token"]
        session = requests.Session()
        return session.get(f"https://api.telegram.org/bot{token}/{method}",
                            params=payload, **kwargs).json()

    def sendMediaGroup(self, media):

        if "media" != []:

            group = {
                "media": json.dumps(media, ensure_ascii=False)
            }

            return self.method("sendMediaGroup", group)
