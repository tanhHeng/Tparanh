from Tparanh.bot.utils.proxy_utils import Proxy
from Tparanh.bot.utils.message_utils import QQMessageContent
from Tparanh.recognizer import ParadigmRecognizerAuto
from Tparanh.bot.utils.decorator_utils import new_thread

recognizer = ParadigmRecognizerAuto()
recognizer.load()

@new_thread()
def on_message(self: Proxy, message):
    content = QQMessageContent(message)
    self.logger.info(content.text)

    if content.reply_msg is not None and content.text == "导":
        reply_content = QQMessageContent(self.get_msg(content.reply_msg))
        if reply_content.user_id != content.user_id:
            return
        if content.images:
            result = []
            for i in content.images:
                result.append(recognizer.recognize_score(self.get_image(i)))
            self.send_msg("\n".join([recognizer.to_plain_text(i) for i in result]), message, cq_reply=True)

def on_updaterecord(self: Proxy, message):
    ...