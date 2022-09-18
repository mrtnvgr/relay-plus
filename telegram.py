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
                "media": json.dumps(media, ensure_ascii=False),
                "disable_notification": True
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
            
            # Get command name
            command = message["text"].split(" ")

            # Help command
            if command[0] == "/help": 
                self.master.tg.sendMessage("Help message placeholder\nwhitelist/blacklist (add,del/delete,list) - control lists")
            
            # Whitelist/Blacklist command
            elif command[0] in ("/whitelist", "/blacklist"):
                
                # Pick list
                vk = self.master.config.config["vk"]
                lst_name = "whitelist" if "/whitelist" == command[0] else "blacklist"
                lst = vk[lst_name]
                
                if len(command)==2:

                    if command[1] == "list":
                        
                        # Send selected list values
                        self.master.tg.sendMessage(f'{lst_name}: {", ".join(lst)}')

                elif len(command)==3:

                    if command[1] == "add":
                        
                        # Check if value already in list
                        if command[2] in lst:
                            self.master.tg.sendMessage(f'Value "{command[2]}" is already in the {lst_name}')
                        else:
                            self.master.config.config["vk"][lst_name].append(command[2])
                            self.master.config.save()
                            self.master.tg.sendMessage(f'Value "{command[2]}" has been added to the {lst_name}')

                    elif command[1] in ("del", "delete"):

                        # Check if value already in list
                        if command[2] in lst:
                            self.master.config.config["vk"][lst_name].remove(command[2])
                            self.master.config.save()
                            self.master.tg.sendMessage(f'Value "{command[2]}" has been deleted from the {lst_name}')
                        else:
                            self.master.tg.sendMessage(f'Value "{command[2]}" is not in the {lst_name}')

