from websocket import WebSocketApp
from Tparanh.bot.utils.proxy_utils import Proxy
from Tparanh.bot.utils.yml_utils import YamlData
from Tparanh.bot.utils.message_utils import QQMessageContent
import logging, json, time

class QQWebSocketClient(WebSocketApp, Proxy):

    def __init__(self, url: str, uin: int, qq_groups: list, admin: list=[], plugins: list = []):
        super().__init__(url, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message)
        Proxy.__init__(self)
        self.config: YamlData
        self.url = url
        self.qq_groups = qq_groups
        self.uin = uin
        self.name = "Tparanh"

        logging.basicConfig(level = logging.DEBUG,format = '[%(asctime)s][%(levelname)s] %(message)s')
        self.logger: logging.Logger = logging.getLogger()

        self.cqhttp_api = classmethod(None)
        self.admin = admin

        self.lang = YamlData("./Tparanh/lang.yml")

        self.plugins = plugins
        self.logger.info(f"Connect to {url}, uin {uin}, listen groups {','.join([str(i) for i in qq_groups])}.")
        self.is_closed = False
    
    def rtr(self, keys) -> str:
        return self.lang.get_nested_value(keys)

    def _on_execute(self, *args, key):
        for i in self.plugins:
            if hasattr(i, key):
                getattr(i, key)(self, *args)
    
    def on_open(self, client):
        self.logger.info("Connected")
        # self.send_group_msg("Bot复活啦~")
    
    def on_close(self, client, close_status_code, close_msg):
        if self.is_closed:
            return
        self.logger.info("Disconnected")
        time.sleep(10)
        self.run_forever()

    def on_message(self, client, message):
        try:
            message = json.loads(message)
            self.on_api_message(message)

            if not ("post_type" in message.keys() and message["post_type"] == "message"):
                return
            
            if not (message["message_type"] == "private" or message["group_id"] in self.qq_groups):
                return

            message = QQMessageContent(message)
            self.logger.debug(message.message)

            if message.user_id in self.admin and message["raw_message"] == "stop":
                self.is_closed = True
                self.close()
            
            self._on_execute(message, key="on_message")
        
        except Exception as e:
            self.logger.warning(message.message if isinstance(message, QQMessageContent) else message)
            raise e
            
    
    def run_forever(self):
        try:
            super().run_forever()
        except KeyboardInterrupt as e:
            self.logger.warning("Closed")
            self.close()

    def start(self):
        self.logger.info("Started.")
        self._on_execute(key="on_start")
        self.run_forever()
        self._on_execute(key="on_close")
        self.logger.info("Closed.")        