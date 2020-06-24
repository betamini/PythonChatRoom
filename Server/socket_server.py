import socket
import select
from threading import Thread

HEADER_LENGTH = 10
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

        while should_run_callable():
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

            for notified_socket in read_sockets:
                if notified_socket is server_socket:
                    client_socket, client_address = server_socket.accept()

                    user = receive_message(client_socket)
                    if user is False:
                        continue

                    sockets_list.append(client_socket)

                    clients[client_socket] = user

                    print(f"Accepted new connection from {client_address[0]}:{client_address[1]} with username {user['data'].decode('utf-8')}")
                    for client_socket in clients:
                        send(encode("System") + encode(f"{user['data'].decode('utf-8')} joind the chatroom"), client_socket, clients)
                else:
                    message = receive_message(notified_socket)

                    if message is False:
                        print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
                        close_connection(notified_socket, sockets_list, clients)
                        continue
                    
                    user = clients[notified_socket]
                    print(f"Recieved message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")

                    for client_socket in clients:
                        if client_socket != notified_socket:
                            send(user['header'] + user['data'] + message['header'] + message['data'], client_socket, clients)

            for notified_socket in exception_sockets:
                print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')} as exception")
                close_connection(notified_socket, sockets_list, clients)
        
        for client_socket in clients:
            close_connection(client_socket, sockets_list, clients)
        
        del clients
        del sockets_list

def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        
        if not len(message_header):
            return False
        message_length = int(message_header.decode("utf-8").strip())
        data = client_socket.recv(message_length)

        print(f"Received {message_header + data}")

        return {"header": message_header, "data": data}
    except:
        return False

def send(data, to_socket, clients):
    print(f"Sent message to {clients[to_socket]['data']} containing: {data}")
    #to_socket.send(data['header'] + data['data'])
    to_socket.send(data)

def encode(raw_data):
    data = str(raw_data).encode("utf-8")
    data_header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
    return data_header + data
    #return {"header": data_header, "data": data}

def close_connection(socket_to_close, sockets_list, clients):
    socket_to_close.close()
    sockets_list.remove(socket_to_close)
    user = clients[socket_to_close]
    del clients[socket_to_close]

    name = encode("System")
    for client_socket in clients:
        send(name + encode(f"{user['data'].decode('utf-8')} exited the chatroom"), client_socket, clients)