from enum import Enum, auto

class UserActionCodes(Enum):
    SEND_MSG = auto() # (message_str)

    START_SERVER = auto() # (ip, port)
    STOP_SERVER = auto() # ()

    MOVE_USER = auto() # (id_to_move, move_to_id)

#class ViewCallCodes(Enum):
#    SERVER_STOPPED = auto() # ()
#    SERVER_STARTED = auto() # ()

class BackendCallCodes(Enum):
    SEND_SYS_MSG = auto() # (message_str)
    SEND_CHAT_AUDIO = auto() # (header_obj, audio_bytearray, origin_user_str, to_socket)
    SEND_CHAT_MSG = auto() # (header_obj, message_bytearray, origin_user_str, to_socket)
    
    SEND_UPDATE_USERS_LISTENING = auto() # ()
    SEND_UPDATE_USERS_ALL = auto() # ()

    PROCESS_DATA = auto() # (data, source_socket)

    #HANDLE_CHAT_MSG = auto() # (header_obj, body_bytearray, from_socket)
    #HANDLE_CHAT_AUDIO = auto() # (header_obj, body_bytearray, from_socket)
    #HANDLE_TALK_REQUEST = auto() # (header_obj, body_bytearray, from_socket)
    #HANDLE_EXIT_ROOM = auto() # (header_obj, body_bytearray, from_socket)
    #HANDLE_SET_USERNAME = auto() # (header_obj, body_bytearray, from_socket)

    MOVE_USER = auto() # (id_to_move, move_to_id)

    START_SERVER = auto() # (ip, port)
    STOP_SERVER = auto() # ()

    ACCEPT_SPECIFIC_SOCKET = auto() # (socket)
    CLOSE_SPECIFIC_SOCKET = auto() # (socket)