from Tparanh.bot.utils.yml_utils import YamlData
from Tparanh.bot.bot import QQWebSocketClient

if __name__ == "__main__":
    config = YamlData("./Tparanh/config.yml")
    bot = QQWebSocketClient(url=config.get("url"), uin=config.get("uin"), qq_groups=config.get("qq_groups"), admin=config.get("admin"))
    bot.start()