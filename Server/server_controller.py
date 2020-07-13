import functools
from enum import Enum, auto

from callback_handler import CallbackHandler

import Server.server_cl as server_cl
import Server.socket_server as socket_server

from Server.server_controller_util import BackendCallCodes, UserActionCodes


callback_handler = CallbackHandler({})

def main():
    global callback_handler
    callback_handler = CallbackHandler({})

    #callback_handler.add_callcodes(ViewCallCodes)
    callback_handler.add_callcodes(BackendCallCodes)
    callback_handler.add_callcodes(UserActionCodes)


    callback_handler.register(UserActionCodes.SEND_MSG, lambda *args: callback_handler.run(BackendCallCodes.SEND_SYS_MSG, *args))
    
    callback_handler.register(UserActionCodes.START_SERVER, lambda *args: callback_handler.run(BackendCallCodes.START_SERVER, *args))
    callback_handler.register(UserActionCodes.STOP_SERVER, lambda : callback_handler.run(BackendCallCodes.STOP_SERVER))
    
    callback_handler.register(UserActionCodes.MOVE_USER, lambda *args: callback_handler.run(BackendCallCodes.MOVE_USER, *args))
    
    server_processor = socket_server.Processor(callback_handler)
    server_action = socket_server.Action(callback_handler, server_processor)
    server_sender = socket_server.Sender(callback_handler)
    #server_back = socket_server.Server(callback_handler)
    server_ui = server_cl.Server_UI(callback_handler)
    server_ui.start_input_loop()

if __name__ == "__main__":
    main()