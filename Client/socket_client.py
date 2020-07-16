import socket
import errno
import json
from threading import Thread
import socket_util
from socket_util import ReturnCode, success, error, connection_broken, should_close
from Client.client_controller_util import BackendCallCodes, ViewCallCodes
from callback_handler import BasicCallCodes

#IP = "127.0.0.1"
#PORT = 20030

callback_handler = None

def handle_socket_util_res(res):
    data, return_code, error_str = res
    if return_code != ReturnCode.SUCCESS:
        if return_code in [ReturnCode.SHOULD_CLOSE, ReturnCode.CONNECTION_BROKEN]:
            callback_handler.run(BasicCallCodes.LOG_ERROR, f"{return_code}::{error_str}")
            callback_handler.run(BasicCallCodes.LOG_DEBUG, "Calling stop() after error in socket_util")
            callback_handler.run(BackendCallCodes.CLOSE_CONNECTION)
        elif return_code is ReturnCode.WARNING:
            callback_handler.run(BasicCallCodes.LOG_WARNING, f"{return_code}::{error_str}")
        else:
            callback_handler.run(BasicCallCodes.LOG_DEBUG, f"{return_code}::{error_str}")
        return None
    return data


class ClientObject():
    def __init__(self, callback_handler_in):
        global callback_handler
        self.client_socket = None
        self._should_listen = False
        callback_handler = callback_handler_in

        self.callback_handler = callback_handler_in

        self.processor = Processor(self.callback_handler)
        self.sender = Sender(self.callback_handler, self)

        self.callback_handler.register(BackendCallCodes.START_CONNECTION, self.start)
        self.callback_handler.register(BackendCallCodes.CLOSE_CONNECTION, self.stop)
    
    # Listen for incomming messages
    def listen(self):
        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Start of listening method/thread")

        # loop over received messages
        while self._should_listen:
            data = handle_socket_util_res(socket_util.receive(self.client_socket))

            self.processor.process(data)
        
        if self.client_socket != None:
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Closing socket from listening method/thread")
            self._close_connection()
        
        self.client_socket = None

        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "End of listening method/thread")

    # Connects to server and starts listening function in a thread
    def start(self, ip, port):
        if self._connect(ip, port):
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Starting listening thread")
            self._should_listen = True
            Thread(target=self.listen, daemon=True).start()
            self.callback_handler.run(ViewCallCodes.CONNECTED_TO_SERVER)
        else:
            return False
    
    def _connect(self, ip, port): 
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #client_socket.setblocking(False)
            self.client_socket.connect((ip, port))
            return True
        except Exception as e:
            self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while trying to establish connection with server with  ip:{ip}  port:{port} Exception: {e}")
            return False
            #return connection_broken(f"Connection error: {str(e)}")
    
    # Makes the listening thread eventualy stop, speeds it up by closing connection -> client_socket.recv() will porbubly return
    def stop(self):
        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Start of stop listening method")

        self._should_listen = False

        if self.client_socket != None:
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Closing socket from stop listening method")
            self._close_connection()

        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "End of stop listening method")
        
        self.client_socket = None
    
    def _close_connection(self):
        self.client_socket

        if self.client_socket != None:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
            self.client_socket = None

        self.callback_handler.run(ViewCallCodes.CONNECTION_CLOSED)
        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Closed socket")


class Processor():
    def __init__(self, callback_handler_in):
        self.callback_handler = callback_handler_in

        self.callback_handler.add_callcodes(["sys_msg_dist", "chat_msg_dist", "chat_audio_dist", "update_users_all", "update_users_listening"])

        self.callback_handler.register("sys_msg_dist", self.process_sys_msg_dist)
        self.callback_handler.register("chat_msg_dist", self.process_chat_msg_dist)
        self.callback_handler.register("chat_audio_dist", self.process_chat_audio_dist)
        self.callback_handler.register("update_users_all", self.process_update_users_all)
        self.callback_handler.register("update_users_listening", self.process_update_users_listening)

    def process(self, data):
        if data != None:
            header_obj, body_ba = data

            if "type" in header_obj:
                msg_type = header_obj["type"]

                if not self.callback_handler.run(msg_type, header_obj, body_ba):
                    self.callback_handler.run(BasicCallCodes.LOG_WARNING, "Unknown message type")
            else:
                self.callback_handler.run(BasicCallCodes.LOG_WARNING, "Can't process data that doesn't contain message type in header")
    
    def process_sys_msg_dist(self, header_obj, body_by):
        message_str = str(handle_socket_util_res(socket_util.deserialize(body_by)))
        if message_str != None:
            self.callback_handler.run(ViewCallCodes.NEW_SYS_MSG, message_str)

    def process_chat_msg_dist(self, header_obj, body_by):
        user_str = header_obj["from_user"]
        message_str = str(handle_socket_util_res(socket_util.deserialize(body_by)))
        if message_str != None:
            self.callback_handler.run(ViewCallCodes.NEW_CHAT_MSG, user_str, message_str)

    def process_chat_audio_dist(self, header_obj, body_by):
        # user_str, stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict
        user_str = header_obj["from_user"]
        level = 0
        next_index = 0
        for b in body_by:
            next_index += 1
            if b == '{'.encode("utf-8")[0]:
                level += 1
            elif b == '}'.encode("utf-8")[0]:
                level -= 1
            if level == 0:
                break
        
        audio_info = handle_socket_util_res(socket_util.deserialize(body_by[:next_index]))

        if audio_info != None:
            #{"frame_count":frame_count, "time_info":time_info, "status":status, "chunk": chunk, "width": width, "channels":channels, "rate":rate} + audiobytes
            rate_int = audio_info["rate"]
            frame_count_int = audio_info["frame_count"]
            width_int = audio_info["width"]
            channels_int = audio_info["channels"]
            chunk_size_int = audio_info["chunk"]
            status_enum = audio_info["status"]
            time_info_dict = audio_info["time_info"]

            stream_bytes = body_by[next_index:]
            if len(stream_bytes) == width_int * chunk_size_int * channels_int:
                self.callback_handler.run(ViewCallCodes.NEW_CHAT_AUDIO, user_str, stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)
            else:
                self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Recieved audio's length does not match the given format")
        else:
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Unable to deserialize audio info")

    def process_update_users_all(self, header_obj, body_by):
        body_obj = handle_socket_util_res(socket_util.deserialize(body_by))
        if body_obj != None:
            if "type" in body_obj:
                if "users" in body_obj:
                    if body_obj["type"] == "full":
                        self.callback_handler.run(ViewCallCodes.UPDATE_USERS_ALL, body_obj["users"])
                if "structure" in body_obj:
                    if body_obj["type"] == "structure":
                        self.callback_handler.run(ViewCallCodes.UPDATE_USERS_STRUCTURE, body_obj["structure"])



    def process_update_users_listening(self, header_obj, body_by):
        body_obj = handle_socket_util_res(socket_util.deserialize(body_by))
        if body_obj != None:
            if "can_listen" in body_obj and "can_speak" in body_obj:
                self.callback_handler.run(ViewCallCodes.UPDATE_USERS_LISTENING, body_obj["can_listen"], body_obj["can_speak"])


class Reciever():
    def __init__(self):
        pass


class Sender():
    def __init__(self, callback_handler_in, clientobject):
        self.callback_handler = callback_handler_in
        self.clientobject = clientobject

        self.callback_handler.register(BackendCallCodes.SEND_CHAT_MSG, self.send_chat_msg)
        self.callback_handler.register(BackendCallCodes.SEND_CHAT_AUDIO, self.send_audiochunk)
        self.callback_handler.register(BackendCallCodes.SEND_TALK_REQUEST, self.send_talk_request)
        self.callback_handler.register(BackendCallCodes.SET_USERNAME, self.set_username)
        self.callback_handler.register(BackendCallCodes.EXIT_ROOM, self.exit_room)
        

    def send_talk_request(self, move_to_id):
        handle_socket_util_res(socket_util.send({"type":"talk_request"}, handle_socket_util_res(socket_util.serialize(move_to_id)), self.clientobject.client_socket))

    def exit_room(self):
        handle_socket_util_res(socket_util.send({"type":"exit_room"}, None, self.clientobject.client_socket, False))

    def send_chat_msg(self, message):
        handle_socket_util_res(socket_util.send({"type":"chat_msg_post"}, handle_socket_util_res(socket_util.serialize(message)), self.clientobject.client_socket))

    def send_audiochunk(self, audiobytes, rate, frame_count, width, channels, chunk, status, time_info): # (stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)
        handle_socket_util_res(socket_util.send( \
            {"type":"chat_audio_post"}, \
            handle_socket_util_res(socket_util.serialize({"frame_count":frame_count, "time_info":time_info, "status":status, "chunk": chunk, "width": width, "channels":channels, "rate":rate})) + audiobytes, \
            self.clientobject.client_socket \
            ))

    def set_username(self, username):
        handle_socket_util_res(socket_util.send({"type":"set_username"}, handle_socket_util_res(socket_util.serialize(username)), self.clientobject.client_socket))