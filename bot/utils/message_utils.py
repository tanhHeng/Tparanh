import logging, os
logger = logging.getLogger()

class QQMessageContent:

    def __init__(self, message):
        img_idx = 0
        self.message = message
        self.id = message["message_id"]
        self.text = ""
        self.images = []
        self.files = []
        self.videos = []
        self.reply_msg = None
        self.user_id = message["user_id"]
        self.is_private = message["message_type"] == "private"
        self.is_group = message["message_type"] == "group"
        self.group_id = message["group_id"] if self.is_group else None
        for i in message["message"]:
            data_type = str(i["type"])
            if data_type == "text":
                self.text += i["data"]["text"]
            elif data_type == "image":
                self.text += f"<#image{img_idx}>"
                img_idx += 1
                self.images.append(i["data"]["file"])
            elif data_type == "file":
                self.files.append(i["data"])
            elif data_type == "reply":
                self.reply_msg = i["data"]["id"]
            elif data_type == "video":
                self.videos.append(i["data"])
            else:
                logger.debug(message)
                logger.debug(f"Message with mismatched type: {data_type}")
    
    def __getitem__(self, key):
        return self.message[key]