import socket
import errno
import json
from threading import Thread

#HEADER_LENGTH = 10
HEADER_LENGTH = 2
#IP = "127.0.0.1"
#PORT = 20030

client_socket = None

def connect(ip, port, raw_username, error_callback): 
    global client_socket

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_socket.setblocking(False)
    #socket.SocketKind.SOCK_STREAM
    try:
        client_socket.connect((ip, port))
    except Exception as e:
        error_callback(f"Connection error: {str(e)}")
        return False
    

    #username = raw_username.encode("utf-8")
    #username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
    #client_socket.send(username_header + username)
    set_username(raw_username)
    #send(raw_username)

    return True

def send_chat_msg(message):
    send(json.dumps({"type":"chat_msg_post", "body":str(message)}))

def set_username(username):
    send(json.dumps({"type":"set_username", "body":str(username)}))

def send(message):
    message = message.encode("utf-8")
    #message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
    message_header = len(message).to_bytes(2, 'big')
    client_socket.send(message_header + message)


# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(incoming_message_callback, error_callback, should_run_callable):
    Thread(target=listen, args=(incoming_message_callback, error_callback, should_run_callable), daemon=True).start()

# Listens for incomming messages
def listen(incoming_message_callback, error_callback, should_run_callable):
    global client_socket

    while should_run_callable():

        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            while should_run_callable():

                # Receive our "header" containing username length, it's size is defined and constant
                username_header = client_socket.recv(HEADER_LENGTH)

                # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                if not len(username_header):
                    error_callback('Connection closed by the server')

                # Convert header to int value
                #username_length = int(username_header.decode('utf-8').strip())
                #username_length = int.from_bytes(username_header, 'big')
                data_length = int.from_bytes(username_header, 'big')

                # Receive and decode username
                #username = client_socket.recv(username_length).decode('utf-8')
                data = json.loads(client_socket.recv(data_length))

                # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                #message_header = client_socket.recv(HEADER_LENGTH)
                #message_length = int(message_header.decode('utf-8').strip())
                #message_length = int.from_bytes(message_header, 'big')
                #message = client_socket.recv(message_length).decode('utf-8')

                # Print message
                if data["type"] == 'chat_msg_dist':
                    incoming_message_callback(data["from_user"], data["body"], data["type"])
                elif data["type"] == 'sys_msg_dist':
                    incoming_message_callback("", data["body"], data["type"])
                else:
                    print("Unkknown messege type")

                #incoming_message_callback(username, message)

        except Exception as e:
            # Any other exception - something happened, exit
            error_callback('Reading error: {}'.format(str(e)))
    
    client_socket.close()
    client_socket = None
