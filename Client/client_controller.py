import functools
from enum import Enum, auto

from callback_handler import CallbackHandler

import Client.chatroom as chatroom
import Client.audiohelper as audiohelper
import Client.socket_client as socket_client

from Client.client_controller_util import ViewCallCodes, BackendCallCodes, UserActionCodes


callback_handler = CallbackHandler({})


def main():
    global callback_handler
    callback_handler = CallbackHandler({})

    callback_handler.add_callcodes(ViewCallCodes)
    callback_handler.add_callcodes(BackendCallCodes)
    callback_handler.add_callcodes(UserActionCodes)


    callback_handler.register(UserActionCodes.SEND_MSG, lambda *args: callback_handler.run(BackendCallCodes.SEND_CHAT_MSG, *args))
    
    callback_handler.register(UserActionCodes.JOIN, lambda *args: callback_handler.run(BackendCallCodes.START_CONNECTION, *args))
    callback_handler.register(UserActionCodes.EXIT_SERVER, lambda *args: callback_handler.run(BackendCallCodes.CLOSE_CONNECTION, *args))
    
    callback_handler.register(UserActionCodes.SET_USERNAME, lambda *args: callback_handler.run(BackendCallCodes.SET_USERNAME, *args))

    callback_handler.register(UserActionCodes.SEND_TALK_REQUEST, lambda *args: callback_handler.run(BackendCallCodes.SEND_TALK_REQUEST, *args))
    callback_handler.register(UserActionCodes.EXIT_ROOM, lambda *args: callback_handler.run(BackendCallCodes.EXIT_ROOM, *args))


    audiohelper.setup(callback_handler, functools.partial(callback_handler.run, BackendCallCodes.SEND_CHAT_AUDIO))
    clientobject = socket_client.ClientObject(callback_handler)
    chatroom.setup(callback_handler)

if __name__ == "__main__":
    main()