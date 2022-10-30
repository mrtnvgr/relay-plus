import json, os


class Config:
    def __init__(self, master):
        """Config class init"""
        self.master = master
        self.load()

    def load(self):
        """Load config"""

        # Pick config name
        if os.path.exists("custom.json"):
            self.path = "custom.json"

        elif os.path.exists("config.json"):
            self.path = "config.json"

        else:
            self.path = None

        # Load config json
        if self.path:
            self.config = json.load(open(self.path))
        else:
            vk_token = self.master.log.warning("VK CALLS API TOKEN: ", func=input)

            telegram_token = self.master.log.warning("TELEGRAM BOT TOKEN: ", func=input)
            telegram_user_id = self.master.log.warning("TELEGRAM USER ID: ", func=input)
            telegram_api_id = self.master.log.warning("TELEGRAM API ID: ", func=input)
            telegram_api_hash = self.master.log.warning(
                "TELEGRAM API HASH: ", func=input
            )
            self.config = {
                "vk": {"token": vk_token},
                "telegram": {
                    "token": telegram_token,
                    "user_id": telegram_user_id,
                    "api_id": telegram_api_id,
                    "api_hash": telegram_api_hash,
                },
            }

        # Check config integrity
        self.check()

    def save(self):
        """Save config"""

        # None => default value
        if self.path == None:
            self.path = "config.json"

        return json.dump(self.config, open(self.path, "w"), indent=4)

    def check(self):
        """Check config"""

        # Check vk and telegram token keys
        for value in ("vk", "telegram"):

            # Check for value key
            if value not in self.config:
                self.config[value] = {}

            # Check for token in value key
            if "token" not in self.config[value]:
                self.master.log.error(f"Specify {value} token")
                self.config[value]["token"] = "TOKEN_HERE"
                self.save()
                exit(1)

        # Check for vk keys
        keys = (
            ("timeout", 1800),
            ("maxHistory", 100),
            ("whitelist", [""]),
            ("blacklist", []),
            ("history", []),
            ("post_types", {"albums": True, "articles": True, "offtopic": True, "donut": True}),
        )

        for key, value in keys:

            if key not in self.config["vk"]:
                self.config["vk"][key] = value

        self.save()

    def addHistory(self, post):
        count = self.config["vk"]["maxHistory"]
        self.config["vk"]["history"].append(post)
        self.config["vk"]["history"] = self.config["vk"]["history"][:count]
        self.save()
