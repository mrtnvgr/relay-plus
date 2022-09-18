#!/usr/bin/env python

import config
import util
import telegram
import vk
import logger

class Main:
    def __init__(self):
        self.log = logger.Logger(silent=False)
        util.fixcwd()
        self.log.info("Loading config...")
        self.config = config.Config(self)
        self.vk = vk.Vk(self.config.config)
        self.tg = telegram.TelegramAPI(self.config.config)
        self.log.info("Starting threads...")
        self.startThreads()

    def startThreads(self):
        self.log.info("Starting vk thread...")
        self.vk_thread = vk.VkListener(self)
        self.vk_thread.start()

        self.log.info("Starting telegram thread...")
        self.tg_thread = telegram.TelegramListener(self)
        self.tg_thread.start()

        self.vk_thread.join()
        self.tg_thread.join()

def main():
    Main()

if __name__ == "__main__":
    main()
