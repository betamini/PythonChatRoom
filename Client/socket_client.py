import socket
import errno
import json
from threading import Thread
import pyaudio
import socket_util

#IP = "127.0.0.1"
#PORT = 20030

client_socket = None

# Returns
# (error_trigger_bool, error_str)
def connect(ip, port, raw_username): 
    global client_socket

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_socket.setblocking(False)
    #socket.SocketKind.SOCK_STREAM
    try:
        client_socket.connect((ip, port))
    except Exception as e:
        return (True, f"Connection error: {str(e)}")
    
    set_username(raw_username)

    return (False, None)

def send_chat_msg(message):
    send({"type":"chat_msg_post"}, message.encode("utf-8"))

def send_audiochunk(audiobytes, frame_count, time_info, status, chunk, width, channels, rate):
    send({"type":"chat_audio_post", "frame_count":frame_count, "time_info":time_info, "status":status, "chunk": chunk, "width": width, "channels":channels, "rate":rate}, audiobytes)

def set_username(username):
    send({"type":"set_username"}, username.encode("utf-8"))

def send(pyobject, body_bytearray=bytearray()):
    pyobject["Content-Length"] = len(body_bytearray)
    header_str = json.dumps(pyobject)

    print(f"Sending {header_str}")

    header_ba = header_str.encode("utf-8")
    fixed_length_header = len(header_ba).to_bytes(2, 'big')
    client_socket.send(fixed_length_header + header_ba + body_bytearray)

# Starts listening function in a thread
# callback_dict - dictionary of callback methods
# error_callback - callback to be called on error
def start_listening(callback_dict, error_callback, should_run_callable):
    print("Starting listening thread")
    Thread(target=listen, args=(callback_dict, error_callback, should_run_callable), daemon=True).start()

# Listens for incomming messages
def listen(callback_dict, error_callback, should_run_callable):
    print("Start of listening method/thread")
    global client_socket

    # Now we want to loop over received messages (there might be more than one) and print them
    while should_run_callable():
        header_obj, body_ba, error_str = socket_util.receive_message(client_socket)

        if error_str is not None:
            error_callback(error_str)
            break

        if header_obj["type"] in callback_dict:
            callback_dict[header_obj["type"]](header_obj, body_ba)
        else:
            print("Unknown message type")

    client_socket.close()
    client_socket = None

    print("End of listening method/thread")
