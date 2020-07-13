from enum import Enum, auto

class UserActionCodes(Enum):
    SEND_MSG = auto() # (message_str)
    TEST_AUDIO = auto() # (seconds_int)
    START_AUDIO = auto() # ()
    STOP_AUDIO = auto() # ()

    JOIN = auto() # (ip, port)
    EXIT_SERVER = auto() # ()

    SET_USERNAME = auto() # (username_str)

    SEND_TALK_REQUEST = auto() # (username_str)
    EXIT_ROOM = auto() # ()

class ViewCallCodes(Enum):
    NEW_CHAT_AUDIO = auto() # (user_str, stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)
    NEW_CHAT_MSG = auto() # (user_str, message_str)
    NEW_SYS_MSG = auto() # (message_str)

    CONNECTION_CLOSED = auto() # ()
    CONNECTED_TO_SERVER = auto() # ()
    
    UPDATE_AUDIO_STATUS = auto() # (is_recording_bool)
    UPDATE_USERS_LISTENING = auto() # (can_listen, can_speak)
    UPDATE_USERS_STRUCTURE = auto() # (list of lists and items ... ...)
    UPDATE_USERS_ALL = auto() # (users)
    UPDATE_USERNAME = auto() # (username_str)

class BackendCallCodes(Enum):
    SEND_CHAT_MSG = auto() # (message_str)
    SEND_CHAT_AUDIO = auto() # (stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)

    START_CONNECTION = auto() # (ip, port)
    CLOSE_CONNECTION = auto() # ()

    SET_USERNAME = auto() # (username_str)

    SEND_TALK_REQUEST = auto() # (username_str)
    EXIT_ROOM = auto() # ()