import json, time
import cv2

class Proxy:

    # 响应api返回值
    def on_api_message(self, message):
        keys = list(message.keys())
        if "echo" in keys:
            exec(f"self.cqhttp_api.{message['echo']} = message")
            self.logger.debug("$ %s $"%eval(f"self.cqhttp_api.{message['echo']}"), module_name = f"cqhttp-api/{message['echo']}")

    # 按qq号获取群聊中指定成员的信息
    def get_group_member_info(self, group_id, user_id):
        '''get qq group member info by user id'''
        try:
            self.cqhttp_api.get_group_member_info = None
            Params = {
    "action": "get_group_member_info",
    "params": {
        "group_id": group_id,
        "user_id": user_id
    },
    "echo": "get_group_member_info"
}
            self.send(json.dumps(Params))
            while self.cqhttp_api.get_group_member_info == None:
                time.sleep(0.01)
            return self.cqhttp_api.get_group_member_info
        except Exception as e:
            self.logger.warn("Failed to call api.")
    
    # 按消息id获取消息信息
    def get_msg(self, message_id):
        '''get qq message by message id'''
        try:
            self.cqhttp_api.get_msg = None
            Params = {
    "action": "get_msg",
    "params": {
        "message_id": message_id,
    },
    "echo": "get_msg"
    }
            self.send(json.dumps(Params))
            while self.cqhttp_api.get_msg == None:
                time.sleep(0.01)
            return self.cqhttp_api.get_msg
        except Exception as e:
            self.logger.warn("Failed to call api.")

    # 指定群聊id或默认向qq_groups内所有群聊发送信息
    def send_group_msg(self, message, group_id=None):
        try:
            if group_id:
                groups_id = [group_id]
            else:
                groups_id = self.qq_groups
            for group_id in groups_id:
                Params = {
                    "action": "send_group_msg",
                    "params": {
                        "group_id": group_id,
                        "message": message
                    },
                    "echo": "send_group_msg"
                }
                self.send(json.dumps(Params))
        except Exception as e:
            self.logger.warn("Failed to send message to qq groups.")
    
    # 发送私聊消息
    def send_private_msg(self, message, user_id, group_id=None):
        try:
            Params = {
                "action": "send_private_msg",
                "params": {
                    "user_id": user_id,
                    "message": message
                },
                "echo": "send_private_msg"
            }
            if group_id:
                Params["params"]["group_id"] = group_id
            self.send(json.dumps(Params))
        except Exception as e:
            self.logger.warn("Failed to send private message.")
    
    # 按照原message发送私聊/群聊消息
    def send_msg(self, msg: str, message: dict, cq_reply: bool = False, cq_at: bool = False):
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
                    msg = "[CQ:at,qq=%s]"(message["sender"]["user_id"])
                self.send_group_msg(msg, message["group_id"])
                return
        
        return AttributeError("message")
    
    # 向指定群聊发送合并转发信息
    def send_group_forward_msg(self, group_id, messages: dict):
        'messages:{"name":"sender name","uin":"sender qq-id","conetent":"msg" or [{"type":"text","data":{"text":"MSG"}}]}'
        messages = [
                        {
                            "type": "node",
                            "data": {
                                "name": messages["name"],
                                "uin": messages["uin"],
                                "content": messages["content"]
                            }
                        }
                    ]
        Params = {
            "action": "send_group_forward_msg",
            "params": {
                "group_id": group_id,
                "messages": messages,
            },
            "echo": "send_group_forward_msg"
        }
        try:
            self.send(json.dumps(Params))
        except Exception as e:
            self.logger.warn("Failed to send forward-message to qq groups.")
    
    def get_image(self, file: str):
        try:
            self.cqhttp_api.get_image = None
            Params = {
                "action": "get_image",
                "params": {
                    "file": file
                },
                "echo": "get_image"
            }
            self.send(json.dumps(Params))
            while self.cqhttp_api.get_image == None:
                time.sleep(0.01)
            return cv2.imread(self.cqhttp_api.get_image["filename"])
        except Exception as e:
            self.logger.warn("Failed to get image.")