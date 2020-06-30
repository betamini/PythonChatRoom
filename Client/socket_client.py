import socket
import errno
import json
from threading import Thread
import pyaudio
import socket_util
from socket_util import ReturnCode, success, error, connection_broken, should_close
from enum import Enum, auto

#IP = "127.0.0.1"
#PORT = 20030

_should_listen = False
client_socket = None
#callback_handler = CallbackHandler({CallCodes.NEW_CHAT_MSG: list(), CallCodes.NEW_CHAT_AUDIO: list(), CallCodes.NEW_SYS_MSG: list(), CallCodes.LOG_DEBUG: list(), CallCodes.LOG_INFO: list(), CallCodes.LOG_WARNING: list(), CallCodes.LOG_ERROR: list(), CallCodes.CONNECTION_CLOSED:list()})
#(origin_user_str, message_str)
class CallbackHandler(dict):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    def register(self, sub_type, function):
        if sub_type in self:
            self[sub_type].append(function)
            return
        print(f"Unable to register {function} to subscribe type {sub_type}: Subscribe type does not exist")
    
    def unregister(self, sub_type, function):
        if sub_type in self:
            if function in self[sub_type]:
                self[sub_type].remove(function)
                return
        print(f"Unable to unregister {function} from subscribe type {sub_type}")
    
    def run(self, sub_type, args):
        if sub_type in self:
            for cb in self[sub_type]:
                cb(args)
            return
        print(f"Unable to run functions in subscribe type {sub_type}: Subscribe type does not exist")

class CallCodes(Enum):
    NEW_CHAT_MSG = auto()
    NEW_CHAT_AUDIO = auto()
    NEW_SYS_MSG = auto()
    LOG_DEBUG = auto()
    LOG_INFO = auto()
    LOG_WARNING = auto()
    LOG_ERROR = auto()
    CONNECTION_CLOSED = auto()

# Returns
# (socket, return_code, error_str)
def _connect(ip, port): 
    global client_socket

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #client_socket.setblocking(False)
        client_socket.connect((ip, port))
        return True
    except Exception as e:
        callback_handler.run(CallCodes.LOG_ERROR, f"Error while trying to establish connection with server with  ip:{ip}  port:{port} Exception: {e}")
        return False
        #return connection_broken(f"Connection error: {str(e)}")
    
def send_chat_msg(message):
    socket_util.send({"type":"chat_msg_post"}, message.encode("utf-8"), client_socket)

def send_audiochunk(audiobytes, frame_count, time_info, status, chunk, width, channels, rate):
    socket_util.send( \
        {"type":"chat_audio_post", "frame_count":frame_count, "time_info":time_info, "status":status, "chunk": chunk, "width": width, "channels":channels, "rate":rate}, \
        audiobytes, \
        client_socket \
        )

def set_username(username):
    socket_util.send({"type":"set_username"}, username.encode("utf-8"), client_socket)

def send(pydict, body_bytearray, to_socket, max_tries=30):
    rep, return_code, error_str = socket_util.send(pydict, body_bytearray, to_socket, max_tries)
    if return_code != ReturnCode.SUCCESS:
        if return_code in [ReturnCode.SHOULD_CLOSE, ReturnCode.CONNECTION_BROKEN]:
            callback_handler.run(CallCodes.LOG_ERROR, f"{return_code}::{error_str}")
            callback_handler.run(CallCodes.LOG_DEBUG, "Calling stop_litening() after error sending message")
            stop()
        elif return_code is ReturnCode.WARNING:
            callback_handler.run(CallCodes.LOG_WARNING, error(return_code, error_str))
        else:
            callback_handler.run(CallCodes.LOG_DEBUG, f"{return_code}::{error_str}")

# Makes the listening thread eventualy stop, speeds it up by closing connection -> client_socket.recv() will porbubly return
def stop():
    global client_socket
    global _should_listen

    callback_handler.run(CallCodes.LOG_DEBUG, "Start of stop listening method")

    _should_listen = False

    if client_socket != None:
        callback_handler.run(CallCodes.LOG_DEBUG, "Closing socket from stop listening method")
        _close_connection()

    callback_handler.run(CallCodes.LOG_DEBUG, "End of stop listening method")
    
    client_socket = None

# Connects to server and starts listening function in a thread
def start(ip, port):
    global _should_listen

    if _connect(ip, port):
        callback_handler.run(CallCodes.LOG_DEBUG, "Starting listening thread")
        _should_listen = True
        Thread(target=listen, daemon=True).start()
        return True
    else:
        stop()
        return False

# Listen for incomming messages
def listen():
    global client_socket
    global callback_handler
    
    callback_handler.run(CallCodes.LOG_DEBUG, "Start of listening method/thread")

    tranlate_dict = {\
        "chat_msg_dist"     :CallCodes.NEW_CHAT_MSG, \
        "chat_audio_dist"   :CallCodes.NEW_CHAT_AUDIO, \
        "sys_msg_dist"      :CallCodes.NEW_SYS_MSG}

    # Now we want to loop over received messages
    while _should_listen:
        data, return_code, error_str = socket_util.receive(client_socket)

        if return_code != ReturnCode.SUCCESS:
            if return_code in [ReturnCode.SHOULD_CLOSE, ReturnCode.CONNECTION_BROKEN]:
                callback_handler.run(CallCodes.LOG_ERROR, f"{return_code}::{error_str}")
                callback_handler.run(CallCodes.LOG_DEBUG, "Listening tread calling stop_litening()")
                stop()
                break
            elif return_code is ReturnCode.WARNING:
                callback_handler.run(CallCodes.LOG_WARNING, f"{return_code}::{error_str}")
            else:
                callback_handler.run(CallCodes.LOG_DEBUG, f"{return_code}::{error_str}")
        else:
            header_obj, body_ba = data

            msg_type = header_obj["type"]

            if msg_type in tranlate_dict:
                callback_handler.run(tranlate_dict[msg_type], data)
            else:
                callback_handler.run(CallCodes.LOG_INFO, "Unknown message type")
    
    if client_socket != None:
        callback_handler.run(CallCodes.LOG_DEBUG, "Closing socket from listening method/thread")
        _close_connection()
    
    client_socket = None

    callback_handler.run(CallCodes.LOG_DEBUG, "End of listening method/thread")

def _close_connection():
    global client_socket

    if client_socket != None:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
        client_socket = None

    callback_handler.run(CallCodes.CONNECTION_CLOSED, False)
    callback_handler.run(CallCodes.LOG_DEBUG, "Closed socket")




callback_handler = CallbackHandler({})

for e in CallCodes:
    callback_handler[e] = list()