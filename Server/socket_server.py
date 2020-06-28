import socket
import select
import queue
import json
from threading import Thread
import socket_util

DATA_LENGTH_LENGTH = 2
index = 0
#IP = "127.0.0.1"
#PORT = 20030

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

        #for i in range

        while should_run_callable():
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

            for notified_socket in exception_sockets:
                print(f"Closed connection from {clients[notified_socket]} as exception")
                close_connection(notified_socket, sockets_list, clients)
            
            for notified_socket in read_sockets:
                if notified_socket is server_socket:
                    client_socket, client_address = server_socket.accept()
                    print(f"{client_address[0]}:{client_address[1]} Connection accepted")

                    #header_obj, body_ba, error_str = socket_util.receive_message(client_socket)
                    #if error_str is not None:
                    #    continue
                    sockets_list.append(client_socket)
                    clients[client_socket] = ""


                    #if header_obj["type"] == "set_username":
                    #    clients[client_socket] = body_ba.decode("utf-8")
                    #else:

                    #if len(message["data"].decode("utf-8")) > 30:
                    #    user["data"] = message["data"].decode('utf-8')[:30].encode('utf-8')

                    #for client_socket in clients:
                    #    rep_body_ba = f"{body_ba.decode('utf-8')} joind the chatroom".encode("utf-8")
                    #    send_to(client_socket, {"type":"sys_msg_dist"}, rep_body_ba)
                        #send_json(json.dumps({"type":"sys_msg_dist", "body":body}), client_socket, clients)
                else:
                    header_obj, body_ba, error_str = socket_util.receive_message(notified_socket)

                    if error_str is not None:
                        print(error_str)
                        print(f"Closing connection from {clients[notified_socket]}")
                        close_connection(notified_socket, sockets_list, clients)
                        print("Connection closed")
                        continue

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

def receive_message(client_socket):
    try:
        #print(f"Recieving message timeout is {client_socket.gettimeout()}")
        fixed_length_header_ba = client_socket.recv(DATA_LENGTH_LENGTH)


        if not len(fixed_length_header_ba):
            return (False, None)
        
        # Minecraft server fun
        # https://wiki.vg/Protocol#Handshaking
        #if raw_data_length[1] == b'\x00' and int(raw_data_length[0], base=0) > 13 and int(raw_data_length[0], base=0) < 24:
        #    data = client_socket.recv(int(raw_data_length[0], base=0) - 1)

        #    data_length = int.from_bytes(raw_data_length, 'big')
        #    data += client_socket.recv(data_length - (int(raw_data_length[0], base=0) - 1))
        
        fixed_length_header_int = int.from_bytes(fixed_length_header_ba, 'big')

        header_obj = json.loads(client_socket.recv(fixed_length_header_int))

        print(f"\nReceived  Length: {fixed_length_header_int}  Data:{header_obj}")
        
        if "Content-Length" in header_obj:
            if header_obj["Content-Length"] is not 0:
                body = client_socket.recv(header_obj["Content-Length"])
                return (header_obj, body)

        return (header_obj, None)
    except Exception as e:
        print(f"Exception while reading data: {e}")
        return (False, None)

def send_to(to_socket, pyobject, body_bytearray=bytearray()):
    pyobject["Content-Length"] = len(body_bytearray)
    header_bytearray = json.dumps(pyobject).encode("utf-8")

    fixed_length_header = len(header_bytearray).to_bytes(2, 'big')
    to_socket.send(fixed_length_header + header_bytearray + body_bytearray)

    print(f"{to_socket.getpeername()[0]}:{to_socket.getpeername()[1]} Sent message  Data: {header_bytearray}")

#def send(data_string, to_socket, clients):
#    data = data_string.encode("utf-8")
#    data_length = len(data).to_bytes(2, 'big')
#    to_socket.send(data_length + data)
#    
#    print(f"Sent message to {clients[to_socket]} Socket: {to_socket} Peername: {to_socket.getpeername()} Sockname: {to_socket.getsockname()}  Data: {data}")

def send_json(json_string, to_socket, clients):
    json_string_length = len(json_string).to_bytes(2, 'big')
    #print(f"Sent message to {clients[to_socket]} containing: {json_string}")
    #print(f"Sent message to {clients[to_socket]} Socket: {to_socket} Peername: {to_socket.getpeername()} Sockname: {to_socket.getsockname()}  Data: {json_string}")
    print(f"{to_socket.getpeername()[0]}:{to_socket.getpeername()[1]} Sent message  Data: {json_string}")
    to_socket.send(json_string_length + json_string.encode("utf-8"))

#def send_raw(raw, to_socket, clients):
#    print(f"Sent message to {clients[to_socket]} containing: {raw}")
#    to_socket.send(raw)

#def encode(raw_data):
#    data = str(raw_data).encode("utf-8")
    #try:
#    data_length = len(data).to_bytes(2, 'big')
    #except OverflowError as e:
    #    print("data is too long, triggeres overflow error")
    #    return False
#    return data_length + data
    #return {"raw_data_length": data_length, "data": data}

def handle_chat_msg_post(user_str, header_obj, body_bytearray, from_socket, clients):
    for client_socket in clients:
        if client_socket != from_socket:
            header_obj["type"] = "chat_msg_dist"
            header_obj["from_user"] = user_str
            send_to(client_socket, header_obj, body_bytearray)
            #send_json(json.dumps(header_obj), client_socket, clients)

def handle_chat_audio_post(user_str, header_obj, body_bytearray, from_socket, clients):
    for client_socket in clients:
        if client_socket != from_socket:
            header_obj["type"] = "chat_audio_dist"
            header_obj["from_user"] = user_str
            send_to(client_socket, header_obj, body_bytearray)
            #send_json(json.dumps(header_obj), client_socket, clients)

def handle_set_username_post(user_str, header_obj, body_bytearray, from_socket, clients):
    desiered_name_str = body_bytearray.decode("utf-8")
    if desiered_name_str is not "":
        availible = True

        for client_socket in clients:
            if clients[client_socket] is desiered_name_str:
                if client_socket is not from_socket:
                    availible = False

        if availible:
            clients[client_socket] = desiered_name_str

            if user_str is "":
                rep_body_ba = f"{body_bytearray.decode('utf-8')} joind the chatroom".encode("utf-8")
            else:
                rep_body_ba = f"{user_str} was renamed to {clients[client_socket]}".encode("utf-8")

            for client_socket in clients:
                send_to(client_socket, {"type":"sys_msg_dist"}, rep_body_ba)
    else:
        send_to(from_socket, {"type":"sys_msg_dist"}, "Username can't be set to empty".encode("utf-8"))

def close_connection(socket_to_close, sockets_list, clients):
    socket_to_close.close()
    sockets_list.remove(socket_to_close)
    user = clients[socket_to_close]
    del clients[socket_to_close]

    for client_socket in clients:
        body_bytearray = f"{user} exited the chatroom".encode("utf-8")
        send_to(client_socket, {"type":"sys_msg_dist"}, body_bytearray)
        #send_json(json.dumps({"type":"sys_msg_dist", "body":body}), client_socket, clients)