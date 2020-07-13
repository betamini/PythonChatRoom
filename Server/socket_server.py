import socket
import select
import queue
import json
from threading import Thread
import socket_util as socket_util
from socket_util import ReturnCode
from callback_handler import BasicCallCodes
from Server.server_controller_util import BackendCallCodes
import Server.room_manager as room_manager

DATA_LENGTH_LENGTH = 2
callback_handler = None

def handle_socket_util_res(res, relevant_socket=None):
    data, return_code, error_str = res
    if return_code != ReturnCode.SUCCESS:
        callback_handler.run(BasicCallCodes.LOG_WARNING, f"{return_code}::{error_str}")
        if return_code in [ReturnCode.SHOULD_CLOSE, ReturnCode.CONNECTION_BROKEN]:
            if relevant_socket != None:
                print(f"Closing connection to {relevant_socket}")
                callback_handler.run(BackendCallCodes.CLOSE_SPECIFIC_SOCKET, relevant_socket)
                #self.close_connection(relevant_socket)
                print("Connection closed")
            else:
                callback_handler.run(BasicCallCodes.LOG_WARNING, f"Connection with a socket should close but no relevant socket was provided")
        return None
    return data

"""
def start(callbackhandler):
    Thread(target=serve,args=callbackhandler, daemon=True).start()

def serve(callbackhandler):
    with ServerObject(callbackhandler) as server_object:
        while should_serve:
            do server stuff

class ServerObject:
    def __enter__():
        pass
    
    def __exit__():
        pass
"""
class SocketsManager(list):
    def __init__(self, callback_handler_in):
        super().__init__()
        self.callback_handler = callback_handler_in

    def __enter__(self):
        self.callback_handler.register(BackendCallCodes.ACCEPT_SPECIFIC_SOCKET, self.accept_specific_socket) # (socket)
        self.callback_handler.register(BackendCallCodes.CLOSE_SPECIFIC_SOCKET, self.close_specific_socket) # (socket)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.callback_handler.unregister(BackendCallCodes.ACCEPT_SPECIFIC_SOCKET, self.accept_specific_socket) # (socket)
        self.callback_handler.unregister(BackendCallCodes.CLOSE_SPECIFIC_SOCKET, self.close_specific_socket) # (socket)
        for wild_socket in self:
            if isinstance(wild_socket, socket.socket):
                if wild_socket.fileno() != -1:
                    try:
                        wild_socket.shutdown(socket.SHUT_RDWR)
                    except OSError as e:
                        self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while trying to shutdown(socket.SHUT_RDWR) {wild_socket} Exception: {e}")
                    wild_socket.close()
        self.clear()
        if not (exc_type == None and exc_value == None and traceback == None):
            self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"SocketManager exited with error!\nExceptionType: {exc_type}\nExceptionValue: {exc_value}\nTraceback: {traceback}")
        return True

    def accept_specific_socket(self, socket_to_accept):
        self.append(socket_to_accept)
    
    # Can't be used in a for loop which loops throug one of the things that it removes the socket from. eg self.socket_list, self.socket_to_uid_and_name
    def close_specific_socket(self, socket_to_close):
        if isinstance(socket_to_close, socket.socket):
            if socket_to_close.fileno() != -1:
                try:
                    socket_to_close.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while trying to shutdown(socket.SHUT_RDWR) {socket_to_close}  Exception: {e}")
                socket_to_close.close()
        self.remove(socket_to_close)

class ServerObject:
    def __init__(self, callback_handler_in, sockets_manager, processor, ip, port):
        global callback_handler
        callback_handler = callback_handler_in
        self.callback_handler = callback_handler_in
        self.sockets_manager = sockets_manager
        self.processor = processor
        
        socket.setdefaulttimeout(0)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.establish_server(ip, port)
        self.sockets_manager.append(self.server_socket)

    def __enter__(self):
        self._should_serve = True
        self.callback_handler.register(BackendCallCodes.STOP_SERVER, self.stop) # ()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.callback_handler.unregister(BackendCallCodes.STOP_SERVER, self.stop) # ()
        self._should_serve = False
        
        if not (exc_type == None and exc_value == None and traceback == None):
            self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Server exited with error!\nExceptionType: {exc_type}\nExceptionValue: {exc_value}\nTraceback: {traceback}")
        return True

    def stop(self):
        self._should_serve = False
        self.server_socket.close()

    def establish_server(self, ip, port):
        try:
            self.server_socket.bind((ip, port))
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, f"Binded Server to  {ip}:{port}")
        except Exception as e:
            self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while trying to bind server_socket to ({ip}:{port})  Exception: {e}")
            raise e

        try:
            self.server_socket.listen()
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, f"Started listening with server")
        except Exception as e:
            self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while starting to listen for connections on server_socket  Addr:({ip}:{port}) Exception: {e}")
            raise e

    def serve(self):
        read_sockets, _, exception_sockets = select.select(self.sockets_manager, [], self.sockets_manager, 60)

        if self._should_serve == False:
            return

        for notified_socket in exception_sockets:
            self.callback_handler.run(BasicCallCodes.LOG_INFO, f"Closing connection from {notified_socket} as exception")
            self.callback_handler.run(BackendCallCodes.CLOSE_SPECIFIC_SOCKET, notified_socket)
            #close_connection(notified_socket)
        
        for notified_socket in read_sockets:
            if notified_socket is self.server_socket:
                client_socket, client_address = self.server_socket.accept()

                self.callback_handler.run(BasicCallCodes.LOG_INFO, f"{client_socket} Connection accepted")
                self.callback_handler.run(BackendCallCodes.ACCEPT_SPECIFIC_SOCKET, client_socket)
            else:
                data = handle_socket_util_res(socket_util.receive(notified_socket), notified_socket)
                self.processor.process(data, notified_socket)
                if data != None:
                    header_obj, body_ba = data

                    if "type" in header_obj:
                        print(f"{notified_socket.getpeername()[0]}:{notified_socket.getpeername()[1]}({notified_socket}) Recieved message  Type: {header_obj['type']}")

                        if header_obj["type"] in self.handle_data_type:
                            self.callback_handler.run(self.handle_data_type[header_obj["type"]], header_obj, body_ba, notified_socket)
                        else:
                            print(f"Unrecougnisable data  Type: {header_obj['type']}")

class Processor():
    def __init__(self, callback_handler_in):
        self.callback_handler = callback_handler_in

        self.callback_handler.add_callcodes(["chat_msg_post", "chat_audio_post", "talk_request", "exit_room", "set_username"])

        self.callback_handler.register("chat_msg_post", self.process_chat_msg_post)
        self.callback_handler.register("chat_audio_post", self.process_chat_audio_post)
        self.callback_handler.register("talk_request", self.process_talk_request)
        self.callback_handler.register("exit_room", self.process_exit_room)
        self.callback_handler.register("set_username", self.process_set_username)

        # TODO
        # Lag en callback til process funksjonen

        # self.handle_data_type = dict()

        # self.handle_data_type['chat_msg_post'] = BackendCallCodes.HANDLE_CHAT_MSG
        # self.handle_data_type['chat_audio_post'] = BackendCallCodes.HANDLE_CHAT_AUDIO
        # self.handle_data_type['set_username'] = BackendCallCodes.HANDLE_SET_USERNAME
        # self.handle_data_type['talk_request'] = BackendCallCodes.HANDLE_TALK_REQUEST
        # self.handle_data_type['exit_room'] = BackendCallCodes.HANDLE_EXIT_ROOM

        # self.callback_handler.register(BackendCallCodes.HANDLE_CHAT_MSG, self.handle_chat_msg_post)  # (header_obj, body_bytearray, from_socket)
        # self.callback_handler.register(BackendCallCodes.HANDLE_CHAT_AUDIO, self.handle_chat_audio_post)  # (header_obj, body_bytearray, from_socket)
        # self.callback_handler.register(BackendCallCodes.HANDLE_SET_USERNAME, self.handle_set_username_post)  # (header_obj, body_bytearray, from_socket)
        # self.callback_handler.register(BackendCallCodes.HANDLE_TALK_REQUEST, self.handle_talk_request)  # (header_obj, body_bytearray, from_socket)
        # self.callback_handler.register(BackendCallCodes.HANDLE_EXIT_ROOM, self.handle_exit_room)  # (header_obj, body_bytearray, from_socket)
    
    def process(self, data, source_socket):
        if data != None:
            header_obj, *body_ba = data

            if "type" in header_obj:
                msg_type = header_obj["type"]

                if not self.callback_handler.run(msg_type, header_obj, body_ba, source_socket):
                    self.callback_handler.run(BasicCallCodes.LOG_WARNING, "Unknown message type {msg_type}")
            else:
                self.callback_handler.run(BasicCallCodes.LOG_WARNING, "Can't process data that doesn't contain message type in header")

    def process_chat_msg_post(self, header_obj, body_by):
        pass
    def handle_chat_msg_post(self, _, body_bytearray, source_socket):
        source_item = self.itemmanager.get_item(source_socket)
        source_socket, source_name_str = source_item.data
        for dest_item in self.roommanager.get_items_near(source_item, True):
            dest_socket, dest_str = dest_item.data
            self.callback_handler.run(BackendCallCodes.SEND_CHAT_MSG, None, body_bytearray, source_name_str, dest_socket)
    

    def process_chat_audio_post(self, header_obj, body_by):
        pass
    def handle_chat_audio_post(self, _, body_bytearray, source_socket):
        source_item = self.itemmanager.get_item(source_socket)
        source_socket, source_name_str = source_item.data
        for dest_item in self.roommanager.get_items_near(source_item, True):
            dest_socket, dest_str = dest_item.data
            self.callback_handler.run(BackendCallCodes.SEND_CHAT_AUDIO, None, body_bytearray, source_name_str, dest_socket)
    

    def process_talk_request(self, header_obj, body_by):
        pass
    def handle_talk_request(self, header_obj, body_bytearray, from_socket):
        data = handle_socket_util_res(socket_util.deserialize(body_bytearray), from_socket)
        if data != None:
            desierd_talk_item = self.itemmanager.get_item(data)
            if desierd_talk_item != None:
                self.move_user(self.itemmanager.get_item(from_socket), desierd_talk_item)
            else:
                self.callback_handler.run(BasicCallCodes.LOG_DEBUG, "Can't go to a room with someone who does not exist")
                self.send_sys_msg(handle_socket_util_res(socket_util.serialize("Can't start a conversation with someone who doesn't exist")), from_socket)

    def process_exit_room(self, header_obj, body_by):
        pass
    def handle_exit_room(self, _, body_bytearray, from_socket):
        self.roommanager.exit_room(self.itemmanager.get_item(from_socket))
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_ALL)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_LISTENING)

    def process_set_username(self, header_obj, body_by):
        pass
    def handle_set_username_post(self, _, body_bytearray, source_socket):
        desiered_name_str = handle_socket_util_res(socket_util.deserialize(body_bytearray))
        self.set_username(source_socket, desiered_name_str)


class Action():
    def __init__(self, callback_handler_in):
        self.callback_handler = callback_handler_in

        self.itemmanager = room_manager.ItemManager()
        self.roommanager = room_manager.RoomManager(self.itemmanager)
        
        self.callback_handler.register(BackendCallCodes.MOVE_USER, self.move_user)  # (source_item, destination_item)
        self.callback_handler.register(BackendCallCodes.SEND_UPDATE_USERS_ALL, self.update_users_all) # ()
        self.callback_handler.register(BackendCallCodes.SEND_UPDATE_USERS_LISTENING, self.update_users_listening) # ()

        self.callback_handler.register(BackendCallCodes.ACCEPT_SPECIFIC_SOCKET, self.accept_specific_socket) # (socket)
        self.callback_handler.register(BackendCallCodes.CLOSE_SPECIFIC_SOCKET, self.close_specific_socket) # (socket)

        self.callback_handler.register(BackendCallCodes.START_SERVER, self.start_server) # (ip, port)
    
    def accept_specific_socket(self, socket_to_accept):
        client_item = self.roommanager.add_item()
        client_item.datakey = [socket_to_accept]
        client_item.data = (socket_to_accept, None)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_ALL)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_LISTENING)

    def close_specific_socket(self, socket_to_close):
        self.roommanager.remove_item(self.itemmanager.get_item(socket_to_close))

        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_ALL)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_LISTENING)

    def move_user(self, source, destination):
        self.roommanager.move_to(source, destination)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_ALL)
        self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_LISTENING)

    def start_server(self, ip, port):
        def serving_loop():
            with SocketsManager(self.callback_handler) as sockets_manager:
                with ServerObject(self.callback_handler, sockets_manager, ip, port) as server:
                    while server._should_serve:
                        server.serve()
            self.callback_handler.run(BasicCallCodes.LOG_DEBUG, f"Server thread ended")
            

        Thread(target=serving_loop, daemon=True).start()
        self.callback_handler.run(BasicCallCodes.LOG_DEBUG, f"Started serving thread")

    def update_users_all(self):
        self.roommanager.print_formated()
        
        users = set()
        for item in self.roommanager.get_all_items():
            users.add(item.data[1])

        for item in self.roommanager.get_all_items():
            temp = users.copy()
            temp.remove(item.data[1])
            header = {"type": "update_users_all"}
            content = {"type":"full", "users": list(temp)}

            body_bytearray = handle_socket_util_res(socket_util.serialize(content), item.data[0])
            handle_socket_util_res(socket_util.send(header, body_bytearray, item.data[0]))
        
        structure = self.make_modified_structure_thing(self.roommanager.get_structure())

        for item in self.roommanager.get_all_items():
            header = {"type": "update_users_all"}
            content = {"type":"structure", "structure": structure}

            body_bytearray = handle_socket_util_res(socket_util.serialize(content), item.data[0])
            handle_socket_util_res(socket_util.send(header, body_bytearray, item.data[0]))

    def make_modified_structure_thing(self, structure_list):
        new_list = list()
        for entry in structure_list:
            if isinstance(entry, list):
                new_list.append(self.make_modified_structure_thing(entry))
            else:
                new_list.append(entry.data[1])
        return new_list

    def update_users_listening(self):
        self.roommanager.print_formated()
        content = dict()
        for item in self.roommanager.get_all_items():
            item_socket, item_name = item.data
            can_listen = self.roommanager.get_items_near(item, True)
            can_speak = self.roommanager.get_items_near(item, False)
            
            #print(can_listen)
            can_listen_pros = list()
            for can_listen_item in can_listen:
                can_listen_pros.append(can_listen_item.data[1])
            #print(can_speak)
            can_speak_pros = list()
            for can_speak_item in can_speak:
                can_speak_pros.append(can_speak_item.data[1])
            
            content = {"can_listen": can_listen_pros, "can_speak": can_speak_pros}
            body_bytearray = handle_socket_util_res(socket_util.serialize(content), item_socket)
            handle_socket_util_res(socket_util.send({"type":"update_users_listening"}, body_bytearray, item_socket), item_socket)
    
    def set_username(self, requesting_socket, desiered_name_str):
        try:
            temp = int(desiered_name_str)
            self.send_sys_msg(handle_socket_util_res(socket_util.serialize("Username can't be only numbers")), requesting_socket)
        except Exception as e:
            req_item = self.itemmanager.get_item(requesting_socket)
            req_socket, req_item_name = req_item.data
            if desiered_name_str == "" or len(desiered_name_str) > 30 or not isinstance(desiered_name_str, str):
                self.send_sys_msg(handle_socket_util_res(socket_util.serialize("Username can't be empty or longer then 30 characters")), requesting_socket)
            else:
                availible = True

                if self.itemmanager.get_item(desiered_name_str) != None:
                    availible = False
                    self.send_sys_msg(handle_socket_util_res(socket_util.serialize("Someone already has that username")), requesting_socket)

                if availible:
                    req_item.data = (req_socket, desiered_name_str)
                    req_item.datakey = [req_socket, desiered_name_str]

                    if req_item_name == None:
                        rep_body_str = f"{desiered_name_str} joined the chatroom"
                    else:
                        rep_body_str = f"{req_item_name} was renamed to {desiered_name_str}"

                    self.callback_handler.run(BackendCallCodes.SEND_SYS_MSG, rep_body_str)
                    self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_ALL)
                    self.callback_handler.run(BackendCallCodes.SEND_UPDATE_USERS_LISTENING)

class Sender():
    def __init__(self, callback_handler_in):
        self.callback_handler = callback_handler_in

        self.callback_handler.register(BackendCallCodes.SEND_SYS_MSG, self.brodcast_sys_msg) # (message_str)
        self.callback_handler.register(BackendCallCodes.SEND_CHAT_MSG, self.send_chat_msg) # (_, message_bytearray, origin_user_str, to_socket)
        self.callback_handler.register(BackendCallCodes.SEND_CHAT_AUDIO, self.send_chat_audio) # (_, audio_bytearray, origin_user_str, to_socket)

    def brodcast_sys_msg(self, message_str):
        message_bytearray = handle_socket_util_res(socket_util.serialize(message_str))
        if message_bytearray != None:
            for item in self.roommanager.get_all_items():
                client_socket, _ = item.data
                self.send_sys_msg(message_bytearray, client_socket)

    #def brodcast_to(list_to_brodcast, blacklist, function, args):

    def send_sys_msg(self, message_bytearray, to_socket):
        handle_socket_util_res(socket_util.send({"type":"sys_msg_dist"}, message_bytearray, to_socket), to_socket)

    def send_chat_msg(self, _, body_bytearray, source_name_str, dest_socket):
        header_obj = dict()
        header_obj["type"] = "chat_msg_dist"
        header_obj["from_user"] = source_name_str
        handle_socket_util_res(socket_util.send(header_obj, body_bytearray, dest_socket), dest_socket)

    def send_chat_audio(self, _, audio_bytearray, source_name_str, dest_socket):
        header_obj = dict()
        header_obj["type"] = "chat_audio_dist"
        header_obj["from_user"] = source_name_str
        handle_socket_util_res(socket_util.send(header_obj, audio_bytearray, dest_socket), dest_socket)