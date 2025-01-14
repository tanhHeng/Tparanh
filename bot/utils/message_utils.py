class QQMessageContent:

    def __init__(self, message):
        img_idx = 0
        self.text = ""
        self.images = []
        self.reply_msg = None
        self.user_id = message["user_id"]
        for i in message["message"]:
            if i["type"] == "text":
                self.text += i["data"]["text"]
            if i["type"] == "image":
                self.text += f"<#image{img_idx}>"
                img_idx += i
                self.images.append(i["data"]["file"])
            if i["type"] == "reply":
                self.reply_msg = i["data"]["id"]