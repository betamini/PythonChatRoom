import Server.socket_server as socket_server

should_run = True


def should_run_callable():
    return should_run

def error_callback_thing(error_str):
    should_run = False
    print(f"\n\n\n{error_str}\n\n\n")


print("Starting server")

socket_server.start_server("", 12345, error_callback_thing, should_run_callable)

inp = input("Press enter to quit")

should_run = False

print("Exited program")