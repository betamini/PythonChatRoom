import socket
import errno
import json
from threading import Thread
import pyaudio
import socket_util

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
    
    set_username(raw_username)

    return True

def send_chat_msg(message):
    send({"type":"chat_msg_post"}, message.encode("utf-8"))

def send_audiochunk(audiobytes):
    print("Sending audio")
    send({"type":"chat_audio_post"}, audiobytes)

def set_username(username):
    send({"type":"set_username"}, username.encode("utf-8"))

def send(pyobject, body_bytearray=bytearray()):
    pyobject["Content-Length"] = len(body_bytearray)
    header = json.dumps(pyobject).encode("utf-8")
    fixed_length_header = len(header).to_bytes(2, 'big')
    client_socket.send(fixed_length_header + header + body_bytearray)

# Starts listening function in a thread
# callback_dict - dictionary of callback methods
# error_callback - callback to be called on error
def start_listening(callback_dict, error_callback, should_run_callable):
    Thread(target=listen, args=(callback_dict, error_callback, should_run_callable), daemon=True).start()

# Listens for incomming messages
def listen(callback_dict, error_callback, should_run_callable):
    global client_socket

    # Now we want to loop over received messages (there might be more than one) and print them
    while should_run_callable():
        header_obj, body_ba, error_str = socket_util.receive_message(client_socket)

        if header_obj is False:
            error_callback(error_str)
            continue

        if header_obj["type"] in callback_dict:
            callback_dict[header_obj["type"]](header_obj, body_ba)
        else:
            print("Unknown message type")
    
    client_socket.close()
    client_socket = None
