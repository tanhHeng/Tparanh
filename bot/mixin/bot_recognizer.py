from Tparanh.bot.bot import QQWebSocketClient
from Tparanh.bot.utils.message_utils import QQMessageContent
from Tparanh.recognizer import ParadigmRecognizerAuto
from Tparanh.bot.utils.decorator_utils import new_thread
import re, os, json, requests, logging, cv2
import pandas as pd
from typing import Iterable

logger = logging.getLogger()
TOKEN_FILE = "token.json"
MAX_FILESIZE = 52428800 # 50MB

def is_img_file(fileobj):
    return os.path.splitext(fileobj["file"])[1][1:] in ["jpg", "jpeg", "png", "bmp"]

def load_token(filename):
    if not os.path.isfile(filename):
        with open(filename, "w+") as file:
            file.write("{}")
        token_data = {}
    else:
        with open(filename, "r") as file:
            token_data = json.loads(file.read())
    return token_data

def save_token(filename, token_data):
    with open(filename, "w+") as file:
        file.write(json.dumps(token_data, ensure_ascii=False, indent="    "))

def post_record(url, token: str, song_level_id: int, record: int | str):
    if type(record) == str and re.fullmatch(r"[0-9]{7}", record):
        record = int(record)
    if type(record) != int:
        return "成绩识别失败"
    body = {
        "upload_token": token,
        "is_replace": False,
        "play_records": [
            {
            "song_level_id": song_level_id,
            "score": record
            }
        ]
    }
    rep = requests.post(url, json=body)
    if rep.status_code == 201:
        result = json.loads(rep.content)
        rat = result[0]["rating"]/100
        return "√ 上传成功 / 单曲rating: %.02f"%rat
    return "× 上传失败：[%s]"%rep.status_code

def download_songs(url):
    result = requests.get(url)
    if result.status_code != 200:
        raise TypeError("Cannot access songs API")
    result = pd.DataFrame(json.loads(result.content)).set_index("song_level_id")
    return result

def is_version_higher(ver1, ver2):
    list1 = str(ver1).split(".")
    list2 = str(ver2).split(".")
    for i in range(len(list1)) if len(list1) < len(list2) else range(len(list2)):
        if int(list1[i]) == int(list2[i]):
            pass
        elif int(list1[i]) < int(list2[i]):
            return False
        else:
            return True
    # 循环结束，哪个列表长哪个版本号高
    if len(list1) == len(list2):
        return False
    elif len(list1) < len(list2):
        return False
    else:
        return True

def get_latest_version(versions: Iterable):
    ver = "0"
    for i in versions:
        if is_version_higher(i, ver):
            ver = i
    return ver

@new_thread
def on_start(self: QQWebSocketClient):
    global recognizer, token_data
    file = self.config.get_nested_value("mixin.recognizer.songs_file")
    if not os.path.isfile(file):
        self.logger.info(f"File '{file}' not found, try to download songs...")
        data = download_songs(self.config.get_nested_value("mixin.recognizer.songs_file_api"))
        data.to_csv(file)
        version = get_latest_version(data["version"])
        self.logger.info(f"Downloading completed. Current version: {version}")
    recognizer = ParadigmRecognizerAuto(file, config_file=self.config.get_nested_value("mixin.recognizer.config_file"), use_gpu=False)
    recognizer.load()
    token_data = load_token(TOKEN_FILE)


@new_thread
def on_message(self: QQWebSocketClient, message: QQMessageContent):
    reply = lambda x: self.send_msg(x, message, True)
    user_id = str(message.user_id)
    upload_flag = True
    if message.text == "导":
        if message.reply_msg is None:
            reply("请回复要导的图片再发送导哦")
            return
        reply_msg = self.get_msg(message.reply_msg)
        if not reply_msg:
            reply("呜呜...获取回复消息失败...")
            return
        reply_content = QQMessageContent(reply_msg)
        
        if reply_content.user_id != message.user_id:
            if message.user_id not in self.admin:
                reply("不可以给其他人导哦...")
                return
            else:
                upload_flag = False
        if not (reply_content.images or [i for i in reply_content.files if is_img_file(i)]):
            reply("没有成绩图导不出来欸...")
            return
        try:
            result = []
            for i in reply_content.images:
                img = self.get_image(i)
                if img is None:
                    reply("图片失效，请重新发送并在10min内导")
                    return
                result.append((recognizer.recognize(img)))
            for i in reply_content.files:
                if not is_img_file(i):
                    continue
                img = cv2.imread(self.get_file(i["file"]))
                if img is None:
                    reply("图片文件失效，请重新发送并在10min内导")
                    return
                result.append((recognizer.recognize(img)))
            if user_id in token_data.keys():
                reply_msg = ""
                name, token = token_data[user_id].values()
            else:
                reply_msg = "未绑定PRP，仅识别成绩，不进行上传\n发送'bind'查看绑定方法\n"
                upload_flag = False
            url = self.config.get_nested_value("mixin.recognizer.records_api").format(name=name)
            reply_msg += "\n".join([recognizer.to_plain_text(*i)+"\n  "+(post_record(url, token, i[0], i[1]) if upload_flag else "$ 未触发上传") for i in result])
            reply(reply_msg)
            self.logger.info(f"user {user_id} recognized {len(result)} images")
        except Exception as e:
            reply(f"导坏掉了...\n{e}\n*请确认回复的图片为范式结算界面，或尝试发送原图后重新导")
            self.logger.warning(e)
    
    elif message.text[:4] == "bind":
        if len(message.text) == 4:
            reply("bind <name> <token> 以绑定PRP账号\nPRP -> https://prp.icel.site/\n<name>: PRP用户名\n<token>: PRP用户上传成绩token")
            return
        if not re.fullmatch(r"bind\s[^\s]+\s[^\s]+?", message.text):
            reply("bind格式错误...\nbind <name> <token>")
            return
        _, name, token = message.text.split(" ")
        if user_id in token_data.keys():
            reply("你已经绑定过账号了！使用'unbind'解绑")
            return
        token_data[user_id] = {
            "name": name,
            "token": token
        }
        save_token(TOKEN_FILE, token_data)
        if message.is_group:
            self.logger.debug("group msg, try to delete")
            self.delete_msg(message.id)
        else:
            self.logger.debug(f"private msg, {message.is_group} {message.is_private}")
        reply("绑定成功！")
        self.logger.info(f"user {user_id} binds {name} {token}")
        return
    
    elif message.text[:6] == "unbind":
        if not user_id in token_data.keys():
            reply(f"你还没有绑定账号捏）")
        elif len(message.text) == 6:
            reply(f"真的要解绑吗？再次发送'unbind {token_data[user_id]['name']}'以确认解绑")
        elif re.fullmatch(r"unbind\s[^\s]+", message.text):
            _, name = message.text.split(" ")
            if name != (name2 := token_data[user_id]['name']):
                reply(f"解绑用户名不对哦，真的想解绑的话就发送'unbind {name2}'吧")
                return
            token_data.pop(user_id)
            reply(f"解绑成功！")
            save_token(TOKEN_FILE, token_data)
            self.logger.info(f"user {user_id} unbinds {name}")
        else:
            reply("unbind [name] 以确认解绑PRP账号")
    
    elif message.text == "update":
        if not message.user_id in self.admin:
            reply("权限不足")
            return
        else:
            data = download_songs(self.config.get_nested_value("mixin.recognizer.songs_file_api"))
            data.to_csv(self.config.get_nested_value("mixin.songs_file"))
            recognizer.records_file = data
            version = get_latest_version(data["version"])
            reply(f"曲目列表更新完成！当前版本 {version}")
            self.logger.info(f"Admin{message.user_id} updates songs successfully. Current version: {version}")

def on_close(self: QQWebSocketClient):
    recognizer.save()
    self.logger.info("Recognizer config saved.")

def on_updaterecord(self: QQWebSocketClient, message):
    ...