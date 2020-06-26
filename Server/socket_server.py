import socket
import select
import queue
import json
from threading import Thread

DATA_LENGTH_LENGTH = 2
index = 0
#IP = "127.0.0.1"
#PORT = 20030

def start_server(ip, port, error_callback, should_run_callable):
    Thread(target=serve, args=(ip, port, error_callback, should_run_callable), daemon=True).start()

def serve(ip, port, error_callback, should_run_callable):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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

                    message = receive_message(client_socket)
                    if message is False:
                        continue
                    sockets_list.append(client_socket)


                    if message["type"] == "set_username":
                        clients[client_socket] = message["body"]
                    else:
                        clients[client_socket] = "Dummy/Placeholder"

                    #if len(message["data"].decode("utf-8")) > 30:
                    #    user["data"] = message["data"].decode('utf-8')[:30].encode('utf-8')

                    print(f"Accepted new connection from {client_address[0]}:{client_address[1]} with username {message['body']}")
                    for client_socket in clients:
                        #send_raw(encode("System") + encode(f"{user['data'].decode('utf-8')} joind the chatroom"), client_socket, clients)
                        #send("System", client_socket, clients)
                        #send(f"{user['data'].decode('utf-8')} joind the chatroom", client_socket, clients)
                        body = f"{message['body']} joind the chatroom"
                        send_json(json.dumps({"type":"sys_msg_dist", "body":body}), client_socket, clients)
                else:
                    message = receive_message(notified_socket)

                    if message is False:
                        print(f"Closed connection from {clients[notified_socket]}")
                        close_connection(notified_socket, sockets_list, clients)
                        continue
                    
                    user = clients[notified_socket]
                    print(f"Recieved message from {user}: {message}")

                    for client_socket in clients:
                        if client_socket != notified_socket:
                            #send_raw(user['raw_data_length'] + user['data'] + message['raw_data_length'] + message['data'], client_socket, clients)
                            #send(user['data'], client_socket, clients)
                            #send(message['raw_data_length'] + message['data'], client_socket, clients)
                            message["type"] = "chat_msg_dist"
                            message["from_user"] = user
                            send_json(json.dumps(message), client_socket, clients)



        
        for client_socket in clients:
            close_connection(client_socket, sockets_list, clients)
        
        del clients
        del sockets_list

def receive_message(client_socket):
    try:
        raw_data_length = client_socket.recv(DATA_LENGTH_LENGTH)


        if not len(raw_data_length):
            return False
        
        # Minecraft server fun
        # https://wiki.vg/Protocol#Handshaking
        #if raw_data_length[1] == b'\x00' and int(raw_data_length[0], base=0) > 13 and int(raw_data_length[0], base=0) < 24:
        #    data = client_socket.recv(int(raw_data_length[0], base=0) - 1)

        #    data_length = int.from_bytes(raw_data_length, 'big')
        #    data += client_socket.recv(data_length - (int(raw_data_length[0], base=0) - 1))
        
        data_length = int.from_bytes(raw_data_length, 'big')
        data = json.loads(client_socket.recv(data_length))

        print(f"Received data of length {data_length} ({raw_data_length}), Data:{data}")

        #return {"raw_data_length": raw_data_length, "data": data}
        return data
    except:
        return False

def send(data_string, to_socket, clients):
    data = data_string.encode("utf-8")
    data_length = len(data).to_bytes(2, 'big')
    print(f"Sent message to {clients[to_socket]} containing: {data}")
    #to_socket.send(data['header'] + data['data'])
    to_socket.send(data_length + data)

def send_json(json_string, to_socket, clients):
    json_string_length = len(json_string).to_bytes(2, 'big')
    print(f"Sent message to {clients[to_socket]} containing: {json_string}")
    to_socket.send(json_string_length + json_string.encode("utf-8"))

def send_raw(raw, to_socket, clients):
    print(f"Sent message to {clients[to_socket]} containing: {raw}")
    to_socket.send(raw)

def encode(raw_data):
    data = str(raw_data).encode("utf-8")
    #try:
    data_length = len(data).to_bytes(2, 'big')
    #except OverflowError as e:
    #    print("data is too long, triggeres overflow error")
    #    return False
    return data_length + data
    #return {"raw_data_length": data_length, "data": data}

def close_connection(socket_to_close, sockets_list, clients):
    socket_to_close.close()
    sockets_list.remove(socket_to_close)
    user = clients[socket_to_close]
    del clients[socket_to_close]

    #name = encode("System")
    for client_socket in clients:
        #send("System", client_socket, clients)
        #send(f"{user['data'].decode('utf-8')} exited the chatroom", client_socket, clients)
        body = f"{user} exited the chatroom"
        send_json(json.dumps({"type":"sys_msg_dist", "body":body}), client_socket, clients)