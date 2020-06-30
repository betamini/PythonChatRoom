import socket
import select
import queue
import json
from threading import Thread
import socket_util as socket_util
from socket_util import ReturnCode

DATA_LENGTH_LENGTH = 2

def start_server(ip, port, error_callback, should_run_callable):
    Thread(target=serve, args=(ip, port, error_callback, should_run_callable), daemon=True).start()

def serve(ip, port, error_callback, should_run_callable):
    handle_data_type = {}
    handle_data_type['chat_msg_post'] = lambda u_str, h_obj, b_ba, from_socket:handle_chat_msg_post(u_str, h_obj, b_ba, from_socket, clients)
    handle_data_type['chat_audio_post'] = lambda u_str, h_obj, b_ba, from_socket:handle_chat_audio_post(u_str, h_obj, b_ba, from_socket, clients)
    handle_data_type['set_username'] = lambda u_str, h_obj, b_ba, from_socket:handle_set_username_post(u_str, h_obj, b_ba, from_socket, clients)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket.setdefaulttimeout(0)

        server_socket.bind((ip, port))
        server_socket.listen()

        sockets_list = [server_socket]
        clients = {}

        while should_run_callable():
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list, 60)

            for notified_socket in exception_sockets:
                print(f"Closed connection from {clients[notified_socket]} as exception")
                close_connection(notified_socket, sockets_list, clients)
            
            for notified_socket in read_sockets:
                if notified_socket is server_socket:
                    client_socket, client_address = server_socket.accept()
                    print(f"{client_address[0]}:{client_address[1]} Connection accepted")

                    sockets_list.append(client_socket)
                    clients[client_socket] = ""

                else:
                    data, return_code, error_str = socket_util.receive(notified_socket)
                    if return_code != ReturnCode.SUCCESS:
                        print(f"{return_code}::{error_str}")
                        if return_code in [ReturnCode.SHOULD_CLOSE, ReturnCode.CONNECTION_BROKEN]:
                            print(f"Closing connection from {clients[notified_socket]}")
                            close_connection(notified_socket, sockets_list, clients)
                            print("Connection closed")
                    else:
                        header_obj, body_ba = data

                        if "type" in header_obj:
                            user_str = clients[notified_socket]

                            print(f"{notified_socket.getpeername()[0]}:{notified_socket.getpeername()[1]} Recieved message  Type: {header_obj['type']}")

                            if header_obj["type"] in handle_data_type:
                                handle_data_type[header_obj["type"]](user_str, header_obj, body_ba, notified_socket)
                            else:
                                print(f"Unrecougnisable data  Type: {header_obj['type']}")
                         
        for client_socket in clients:
            close_connection(client_socket, sockets_list, clients)
        
        del clients
        del sockets_list

def handle_chat_msg_post(user_str, header_obj, body_bytearray, from_socket, clients):
    for client_socket in clients:
        if client_socket != from_socket:
            send_chat_msg(header_obj, body_bytearray, user_str, client_socket)

def handle_chat_audio_post(user_str, header_obj, body_bytearray, from_socket, clients):
    for client_socket in clients:
        if client_socket != from_socket:
            send_chat_audio(header_obj, body_bytearray, user_str, client_socket)

def handle_set_username_post(user_str, header_obj, body_bytearray, from_socket, clients):
    desiered_name_str = body_bytearray.decode("utf-8")
    if desiered_name_str == "" or len(desiered_name_str) > 30:
        send_sys_msg("Username can't be empty or longer then 30 characters".encode("utf-8"), from_socket)
    else:
        availible = True

        for client_socket in clients:
            if clients[client_socket] is desiered_name_str:
                if client_socket != from_socket:
                    availible = False

        if availible:
            clients[client_socket] = desiered_name_str

            if user_str == "":
                rep_body_str = f"{body_bytearray.decode('utf-8')} joined the chatroom"
            else:
                rep_body_str = f"{user_str} was renamed to {clients[client_socket]}"

            brodcast_sys_msg(rep_body_str, clients)

def brodcast_sys_msg(message_str, clients):
    message_bytearray = message_str.encode("utf-8")
    for client_socket in clients:
        send_sys_msg(message_bytearray, client_socket)

#def brodcast_to(list_to_brodcast, blacklist, function, args):

def send_sys_msg(message_bytearray, to_socket):
    socket_util.send({"type":"sys_msg_dist"}, message_bytearray, to_socket)

def send_chat_msg(header_obj, body_bytearray, origin_user_str, to_socket):
    header_obj["type"] = "chat_msg_dist"
    header_obj["from_user"] = origin_user_str
    socket_util.send(header_obj, body_bytearray, to_socket)

def send_chat_audio(header_obj, audio_bytearray, origin_user_str, to_socket):
    header_obj["type"] = "chat_audio_dist"
    header_obj["from_user"] = origin_user_str
    socket_util.send(header_obj, audio_bytearray, to_socket)

def close_connection(socket_to_close, sockets_list, clients):
    socket_to_close.close()
    sockets_list.remove(socket_to_close)
    user = clients[socket_to_close]
    del clients[socket_to_close]

    brodcast_sys_msg(f"{user} exited the room", clients)
