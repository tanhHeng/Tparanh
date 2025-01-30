import json, time, os
import cv2
from threading import Event
from Tparanh.bot.utils.message_utils import QQMessageContent

class Proxy:

    def __init__(self):
        self.callback = {}

    # 响应api返回值
    def on_api_message(self, message):
        keys = list(message.keys())
        if "status" in keys and message["status"] == "failed":
            self.logger.warning(message)
        if "echo" not in keys:
            return
        id = message["echo"]
        if id != "api":
            self.callback[id][1] = message
            self.callback[id][0].set()
        self.logger.debug("$ %s $"%str(message))

    def _execute_api(self, api_method, _await: bool | int = 10, **kwargs):
        Params = {
            "action": api_method,
            "params": kwargs,
            "echo": "api"
        }
        if _await:
            id = str(time.time())
            event = Event()
            self.callback[id] = [event, None]
            Params["echo"] = id
        # 
        Params = json.dumps(Params, ensure_ascii=False)
        self.logger.debug(Params)
        self.send(Params)
        # self.logger.debug("1")
        if not _await:
            return
        event.wait(_await)
        result = self.callback[id][1]
        self.callback.pop(id)
        if result:
            return result
        else:
            raise TimeoutError(f"Failed to call api '{api_method}': timeout")


    # 按qq号获取群聊中指定成员的信息
    def get_group_member_info(self, group_id, user_id):
        return self._execute_api(api_method="get_group_member_info", group_id = group_id, user_id = user_id)
    
    # 按消息id获取消息信息
    def get_msg(self, message_id):
        '''get qq message by message id'''
        msg = self._execute_api(api_method="get_msg", message_id = message_id)
        if msg and "data" in msg.keys():
            return msg["data"]

    # 指定群聊id或默认向qq_groups内所有群聊发送信息
    def send_group_msg(self, message, group_id=None):
        return self._execute_api("send_group_msg", False, message = message, group_id = [group_id] if group_id else self.qq_groups)
    
    # 发送私聊消息
    def send_private_msg(self, message, user_id, group_id=None):
        if group_id:
            return self._execute_api("send_private_msg", False, message = message, user_id = user_id, group_id = group_id)
        return self._execute_api("send_private_msg", False, message = message, user_id = user_id)
    
    # 按照原message发送私聊/群聊消息
    def send_msg(self, msg: str, message: dict | QQMessageContent, cq_reply: bool = False, cq_at: bool = False):
        if message["post_type"] == "message":

            if cq_reply:
                msg = "[CQ:reply,id=%s]"%(message["message_id"]) + msg

            if message["message_type"] == "private":
                if "group_id" in message["sender"].keys():
                    group_id = message["sender"]["group_id"]
                else:
                    group_id = None
                self.send_private_msg(msg, message["sender"]["user_id"], group_id)
                return 
            elif message["message_type"] == "group":
                if cq_at:
                    msg = "[CQ:at,qq=%s]"%(message["sender"]["user_id"])
                self.send_group_msg(msg, message["group_id"])
                return
        
        return AttributeError("message")
    
    # # 向指定群聊发送合并转发信息
    # def send_group_forward_msg(self, group_id, messages: dict):
    #     'messages:{"name":"sender name","uin":"sender qq-id","conetent":"msg" or [{"type":"text","data":{"text":"MSG"}}]}'
    #     messages = [
    #                     {
    #                         "type": "node",
    #                         "data": {
    #                             "name": messages["name"],
    #                             "uin": messages["uin"],
    #                             "content": messages["content"]
    #                         }
    #                     }
    #                 ]
    #     Params = {
    #         "action": "send_group_forward_msg",
    #         "params": {
    #             "group_id": group_id,
    #             "messages": messages,
    #         },
    #         "echo": "send_group_forward_msg"
    #     }
    #     try:
    #         self.send(json.dumps(Params))
    #     except Exception as e:
    #         self.logger.warn("Failed to send forward-message to qq groups.")
    
    def send_forward_msg_fast(self, contents: list, message: dict | QQMessageContent):
        messages = [{
                        "type": "node",
                        "data": {
                            "content": [
                                {
                                    "type": "text",
                                    "data": {
                                        "text": i
                                    }
                                }
                            ]
                        }
                    } for i in contents]
        if message.is_group:
            self._execute_api("send_group_forward_msg", False, group_id = str(message.group_id), messages = messages)
        elif message.is_private:
            self._execute_api("send_private_forward_msg", False, user_id = str(message.user_id), messages = messages)
    
    def get_image(self, file: str):
        return cv2.imread(self._execute_api("get_image", file = file)["data"]["file"])

    def get_file(self, file: str):
        # return self._execute_api("get_file", file_id = file_id)["data"]["file"]
        return self._execute_api("get_file", file = file)["data"]["file"]
    
    def delete_msg(self, message_id: int):
        return self._execute_api("delete_msg", False, message_id = message_id)
    
    def get_video(self, video_data: dict):
        url, path = video_data["url"], video_data["path"]
        if not os.path.isfile(path):
            self._execute_api("download_file", 60)