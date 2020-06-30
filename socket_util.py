import socket
import json
from enum import Enum, auto

PRE_HEADER_LENGTH = 2

# Returns (header_obj, body_ba, ReturnCode, error_str)
# header_obj == false -> error
def receive(sock):
    #print(f"\n{sock.getpeername()[0]}:{sock.getpeername()[1]}: Trying to receive message")
    print(f"\nTrying to receive message")

    # Receive pre-header bytearray
    pre_header_ba, return_code, error_str = _receive(sock, PRE_HEADER_LENGTH, "pre-header")
    if return_code != ReturnCode.SUCCESS:
        return error(return_code, error_str)
    
    # Convert pre-header to int value
    pre_header_int = int.from_bytes(pre_header_ba, 'big')
    if pre_header_int == 0:
        return should_close("Pre-header value was zero")

    print(f"Received pre-header: {pre_header_int}")

    # Receive header bytearray
    header_ba, return_code, error_str = _receive(sock, pre_header_int, "header")
    if return_code != ReturnCode.SUCCESS:
        return error(return_code, error_str)
    
    # Deserialize header to python dict object
    header_obj, return_code, error_str = deserialize(header_ba)
    if return_code != ReturnCode.SUCCESS:
        return error(return_code, error_str)
    try:
        header_obj = json.loads(header_ba)
    except Exception as e:
        return should_close(f"Exception while decoding header from json to python dict object  Exception: {e}")

    print(f"Received header object: {header_obj}")

    # Receive body bytearray if (Content-Length > 0)
    if "Content-Length" in header_obj:
        if header_obj["Content-Length"] != 0:
            # Receive body
            body_ba, return_code, error_str = _receive(sock, header_obj["Content-Length"], "body")
            if return_code != ReturnCode.SUCCESS:
                return error(return_code, error_str)

    return success((header_obj, body_ba))

def _receive(sock, number_of_bytes_int, type_hint="data"):
    data_ba = bytearray()
    try:
        received_bytes = 0
        while received_bytes < number_of_bytes_int:
            chunk = sock.recv(number_of_bytes_int - received_bytes)
            chunk_length = len(chunk)
            
            if not chunk_length:
                print("Recieved empty message")
                return connection_broken("Recieved empty message. Connection closed by opposit side")

            data_ba.extend(chunk)
            received_bytes += chunk_length
        return success(data_ba)
    except Exception as e:
        return should_close(f"Exception while recieving {type_hint}  Exception: {e}")

# Returns number of cycles needed to transmit data
def send(pydict, body_bytearray, to_socket, max_tries=30):
    if not isinstance(body_bytearray, bytearray) and not isinstance(body_bytearray, bytes):
        if isinstance(body_bytearray, type(None)):
            body_bytearray = bytearray()
        else:
            return warning(f"Can only send body of type bytearray or bytes, actual type {type(body_bytearray)}")
    
    if not isinstance(to_socket, socket.socket):
        return warning(f"Can't send data to a non socket object, actual type {type(to_socket)}")

    if not isinstance(pydict, dict):
        return warning(f"Header can only be a dict, actual type {type(pydict)}")

    print(f"{to_socket.getpeername()[0]}:{to_socket.getpeername()[1]} Sending data")

    # Set length of body in header
    pydict["Content-Length"] = len(body_bytearray)
    
    # Serialize python dict object to bytes
    header_bytearray, return_code, error_str = serialize(pydict)
    if return_code != ReturnCode.SUCCESS:
        return error(return_code, error_str)

    # Find length of header and tranlate to network ordered byte
    fixed_length_header = len(header_bytearray).to_bytes(2, 'big')
    
    # Concat bytes to send
    bytearray_to_send = fixed_length_header + header_bytearray + body_bytearray
    
    # Send bytes to socket
    tries, return_code, error_str = _send(to_socket, bytearray_to_send, max_tries)
    if return_code != ReturnCode.SUCCESS:
        return error(return_code, error_str)

    print(f"{to_socket.getpeername()[0]}:{to_socket.getpeername()[1]} Sending successful in {tries} sending cycles  Data: {header_bytearray}")
    return success(tries)

# Returns number of cycles needed to transmit data
def _send(sock, data_bytearray, max_tries):
    bytes_sent = 0
    curr_try = 0

    while bytes_sent < len(data_bytearray) and max_tries != curr_try:
        bytes_sent += sock.send(data_bytearray[bytes_sent:])
        curr_try += 1

    if curr_try is max_tries:
        print(f"{sock.getpeername()[0]}:{sock.getpeername()[1]} Stopped sending data")
        return should_close(f"Could not send complete data in {curr_try} tries")
    else:
        return success(curr_try)

def deserialize(serialized_dict):
    try:
        deserialized_dict = json.loads(serialized_dict.decode("utf-8"))
        return success(deserialized_dict)
    except Exception as e:
        return should_close(f"Exception while decoding data of type {type(serialized_dict)} from json to python dict object  Exception: {e}")

def serialize(pydict):
    try:
        serialized_bytearray = json.dumps(pydict).encode("utf-8")
        return success(serialized_bytearray)
    except Exception as e:
        return warning(f"Error while serielizing {pydict}  Exception: {e}")

def should_close(error_str):
    return (None, ReturnCode.SHOULD_CLOSE, error_str)

def connection_broken(error_str):
    return (None, ReturnCode.CONNECTION_BROKEN, error_str)

def warning(error_str):
    return (None, ReturnCode.WARNING, error_str)

def error(return_code, error_str):
    return (None, return_code, error_str)

def success(data=None):
    return (data, ReturnCode.SUCCESS, None)

class ReturnCode(Enum):
    SHOULD_CLOSE = auto()
    CONNECTION_BROKEN = auto()
    WARNING = auto()
    SUCCESS = auto()

# Minecraft server fun
# https://wiki.vg/Protocol#Handshaking
#if raw_data_length[1] == b'\x00' and int(raw_data_length[0], base=0) > 13 and int(raw_data_length[0], base=0) < 24:
#    data = client_socket.recv(int(raw_data_length[0], base=0) - 1)

#    data_length = int.from_bytes(raw_data_length, 'big')
#    data += client_socket.recv(data_length - (int(raw_data_length[0], base=0) - 1))