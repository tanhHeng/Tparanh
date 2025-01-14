from websocket import WebSocketApp
from Tparanh.bot.utils.proxy_utils import Proxy
from Tparanh.bot.utils.yml_utils import YamlData
from Tparanh.bot.mixin import bot_recognizer
import logging, json, time


class QQWebSocketClient(WebSocketApp, Proxy):

    def __init__(self, url: str, uin: int, qq_groups: list, admin: list=[]):
        super().__init__(url, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)
        self.url = url
        self.qq_groups = qq_groups
        self.uin = uin

        logging.basicConfig(level = logging.INFO,format = '[%(asctime)s][%(levelname)s] %(message)s')
        self.logger = logging.getLogger()

        self.cqhttp_api = classmethod(None)
        self.admin = admin

        self.lang = YamlData("./Tparanh/lang.yml")

        self.plugins = [bot_recognizer]
    
    def rtr(self, keys) -> str:
        return self.lang.get_nested_value(keys)

    def on_open(self, client):
        self.logger.info("Connected", module_name="Connection")
        self.send_group_msg("Bot复活啦~")
    
    def on_close(self, client, close_status_code, close_msg):
        self.logger.info("Disconnected", module_name="Connection")
        time.sleep(10)
        self.run_forever()

    def on_message(self, client, message):
        try:
            message = json.loads(message)
            try:
                if message["post_type"] != "meta_event":
                    self.logger.debug(message, module_name="Message")
            except:
                pass

            self.on_api_message(message)

            if "post_type" in message.keys() and message["post_type"] == "message":
                for i in self.plugins:
                    if hasattr(i, "on_message"):
                        i.on_message(message)
                pass
        
        except Exception as e:
            self.logger.warning(message, warn=e, module_name="Message")
    
    def run_forever(self):
        try:
            super().run_forever
        except Exception as e:
            self.logger.warning(warn=e,module_name="run-forever")
            self.close()

    def start(self):
        self.run_forever()
        self.logger.info("Started.")