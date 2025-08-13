from protocol.messages.MessageBase import MessageBase

class SubscribeMessage(MessageBase):
    pass

class SubscribeReply(MessageBase):
    uuid: int