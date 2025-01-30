from Tparanh.bot.utils.message_utils import QQMessageContent
from Tparanh.bot.utils.proxy_utils import Proxy

HELP = '''# 帮助|
## PRP绑定
'bind <name> <token>' 绑定PRP账号（建议私聊绑定！！！）
- 发送'bind'以查看用法
'unbind' 解绑PRP账号|
## 上传成绩
- 在打歌结算界面截图，将截图发送到群里或私聊bot（不要发送原图！！！），自己回复自己发的图片'导'即可|
## 管理员指令
- stop 停止bot
- update 更新曲目列表'''.split("|\n")

def on_message(self: Proxy, message: QQMessageContent):
    if not message.text in ["help", "帮助"]:
        return
    self.send_forward_msg_fast(HELP, message)
    # self.send_msg(HELP, message, True)