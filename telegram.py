import threading
import requests
import json
import util

class TelegramAPI:
    def __init__(self, config):
        self.config = config["telegram"]

    def method(self, method, payload, **kwargs):
        payload["chat_id"] = self.config["user_id"]
        token = self.config["token"]
        session = requests.Session()
        response =  session.get(f"https://api.telegram.org/bot{token}/{method}",
                                params=payload, **kwargs).json()
        
        if response["ok"]:
            return response["result"]
        else:
            return response

    def sendMediaGroup(self, media):

        if "media" != []:

            group = {
                "media": json.dumps(media, ensure_ascii=False)
            }

            return self.method("sendMediaGroup", group)

    def sendMessage(self, text):
        return self.method("sendMessage", {"text": text})

class TelegramListener(threading.Thread):
    def __init__(self, master):
        super().__init__(daemon=True)
        self.master = master

    def run(self):
        """ TelegramListener thread main loop"""


        updates_payload = {"timeout": 60000}
        while True:
           
            # Get updates
            updates = self.master.tg.method("getUpdates", updates_payload)

            # Check if any updates
            if updates != []:

                # Error check
                if "error_code" in updates:
                    self.master.log.error(f"telegram: getUpdates: {updates['description']}")
                
                # Set updates offset to payload
                updates_payload["offset"] = updates[-1]["update_id"]+1

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
            if message["text"].startswith("/help"):
                self.master.tg.sendMessage("Help message todo\nupdate - pull updates")

            elif message["text"].startswith("/update"):
                util.update()
