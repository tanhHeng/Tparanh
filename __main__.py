import os, sys
sys.path.append(os.getcwd())

from Tparanh.bot.utils.yml_utils import YamlData
from Tparanh.bot import TparanhBot

if __name__ == "__main__":
    config = YamlData("config.yml")
    bot = TparanhBot(config)
    bot.start()