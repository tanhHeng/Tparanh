from Tparanh.bot.bot import QQWebSocketClient
from Tparanh.bot.mixin import bot_recognizer, download_songs, help_msg

PLUGINS = [bot_recognizer, download_songs, help_msg]

class TparanhBot(QQWebSocketClient):

    def __init__(self, config):
        super().__init__(url=config.get("url"), uin=config.get("uin"), qq_groups=config.get("qq_groups"), admin=config.get("admin"), plugins=PLUGINS)
        self.config = config