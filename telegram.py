import threading
import requests
import json
import util


class TelegramAPI:
    def __init__(self, config):
        self.config = config["telegram"]

    def method(self, method, payload, **kwargs):
        payload["chat_id"] = self.config["user_id"]
        payload["parse_mode"] = "HTML"
        token = self.config["token"]
        session = requests.Session()
        response = session.get(
            f"https://api.telegram.org/bot{token}/{method}", params=payload, **kwargs
        ).json()

        if response["ok"]:
            return response["result"]
        else:
            return response

    def sendMediaGroup(self, media):

        if "media" != []:

            group = {
                "media": json.dumps(media, ensure_ascii=False),
                "disable_notification": True,
            }

            return self.method("sendMediaGroup", group)

    def sendMessage(self, text):
        return self.method("sendMessage", {"text": text})


class TelegramListener(threading.Thread):
    def __init__(self, master):
        super().__init__()
        self.master = master

    def run(self):
        """TelegramListener thread main loop"""

        offset = self.master.config.config["telegram"].get("update_id", 0)
        updates_payload = {"timeout": 60000, "offset": offset}
        while True:

            # Get updates
            try:
                updates = self.master.tg.method("getUpdates", updates_payload)
            except requests.exceptions.ConnectionError:
                continue

            # Error check
            if "error_code" in updates:
                self.master.log.error(f"telegram: getUpdates: {updates['description']}")

            # Check if any updates
            if updates != []:

                # Set updates offset to payload
                try:
                    update_id = int(updates[-1]["update_id"]) + 1

                except KeyError:

                    # Get rid of annoying bad gateway errors
                    if updates["error_code"] != 502:
                        self.master.tg.sendMessage(
                            f"{updates['error_code']}: {updates['description']}"
                        )
                    continue

                # Save current update_id
                self.master.config.config["telegram"]["update_id"] = update_id
                self.master.config.save()

                updates_payload["offset"] = update_id

                # Iterate through updates
                for update in updates:

                    # Check if update from user_id
                    user_id = self.master.config.config["telegram"]["user_id"]

                    if str(update["message"]["from"]["id"]) == str(user_id):

                        # Parse update text
                        self.userCommands(update)

    def userCommands(self, update):

        message = update["message"]

        # Check if text is command
        if message["text"].startswith("/"):

            # Commands

            # Get command name
            command = message["text"].split(" ")

            # Help command
            if command[0] == "/help":
                message = [
                    "RelayPlus (github.com/mrtnvgr/relay-plus)",
                    "whitelist/blacklist - list control",
                    "update - force self update",
                ]
                self.master.tg.sendMessage("\n".join(message))

            # Whitelist/Blacklist command
            elif command[0] in ("/whitelist", "/blacklist"):

                # Pick list
                vk = self.master.config.config["vk"]
                lst_name = "whitelist" if "/whitelist" == command[0] else "blacklist"
                lst = vk[lst_name]

                if len(command) == 2:

                    if command[1] == "list":

                        # Send selected list values
                        self.master.tg.sendMessage(f'{lst_name}: {", ".join(lst)}')

                elif len(command) == 3:

                    if command[1] == "add":

                        # Check if value already in list
                        if command[2] in lst:
                            self.master.tg.sendMessage(
                                f'Value "{command[2]}" is already in the {lst_name}'
                            )
                        else:
                            self.master.config.config["vk"][lst_name].append(command[2])
                            self.master.config.save()
                            self.master.tg.sendMessage(
                                f'Value "{command[2]}" has been added to the {lst_name}'
                            )

                    elif command[1] in ("del", "delete"):

                        # Check if value already in list
                        if command[2] in lst:
                            self.master.config.config["vk"][lst_name].remove(command[2])
                            self.master.config.save()
                            self.master.tg.sendMessage(
                                f'Value "{command[2]}" has been deleted from the {lst_name}'
                            )
                        else:
                            self.master.tg.sendMessage(
                                f'Value "{command[2]}" is not in the {lst_name}'
                            )

            elif command[0] == "/update":

                # Update self
                util.update()
