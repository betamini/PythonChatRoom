import socket
import json

FIXED_LENGTH_HEADER_LENGTH = 2

# Returns (header_obj, body_ba, error_str)
# header_obj == false -> error
def receive_message(sock):
    try:
        print(f"\n{sock.getpeername()[0]}:{sock.getpeername()[1]}: Trying to receive message")

        fixed_length_header_ba = sock.recv(FIXED_LENGTH_HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(fixed_length_header_ba):
            print("Recieved empty message")
            return (False, None, "Recieved empty message. Connection closed by opposit side")
        
        # Convert header to int value
        fixed_length_header_int = int.from_bytes(fixed_length_header_ba, 'big')
        print(f"Received fixed length header: {fixed_length_header_int}")
        
        header_obj = json.loads(sock.recv(fixed_length_header_int))
        print(f"Received header object: {header_obj}")

        if "Content-Length" in header_obj:
            if header_obj["Content-Length"] is not 0:
                body_ba = sock.recv(header_obj["Content-Length"])
                return (header_obj, body_ba, None)

        return (header_obj, bytearray(), None)
    except Exception as e:
        return (False, None, f"Exception while recieving or decoding data  Exception: {e}")



# Minecraft server fun
# https://wiki.vg/Protocol#Handshaking
#if raw_data_length[1] == b'\x00' and int(raw_data_length[0], base=0) > 13 and int(raw_data_length[0], base=0) < 24:
#    data = client_socket.recv(int(raw_data_length[0], base=0) - 1)

#    data_length = int.from_bytes(raw_data_length, 'big')
#    data += client_socket.recv(data_length - (int(raw_data_length[0], base=0) - 1))