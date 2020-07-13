import Server.socket_server as socket_server
from Server.server_controller_util import UserActionCodes
from callback_handler import BasicCallCodes

class Server_UI:
    def __init__(self, callback_handler_in):
        self.callback_handler = callback_handler_in

        self.callback_handler.register(BasicCallCodes.LOG_DEBUG, lambda msg_str:print(f"DEBUG: {msg_str}"))
        self.callback_handler.register(BasicCallCodes.LOG_INFO, lambda msg_str:print(f"INFO: {msg_str}"))
        self.callback_handler.register(BasicCallCodes.LOG_WARNING, lambda msg_str:print(f"WARN: {msg_str}"))
        self.callback_handler.register(BasicCallCodes.LOG_ERROR, lambda msg_str:print(f"ERROR: {msg_str}"))

        self.thing = dict()

        self.thing["h"] = {"help":["", "display this"], "run": lambda args: self.display_help()}
        self.thing["quit"] = {"help":["", "quit the application"], "run": lambda args: self.quit_loop()}
        self.thing["start"] = {"help":["ip port", "start server"], "run": lambda args: self.callback_handler.run(UserActionCodes.START_SERVER, args[0], int(args[1]))}
        self.thing["stop"] = {"help":["", "stop server"], "run": lambda args: self.callback_handler.run(UserActionCodes.STOP_SERVER)}
        self.thing["msg"] = {"help":["message", "send system message"], "run": lambda args: self.callback_handler.run(UserActionCodes.SEND_MSG, ' '.join(args))}
        self.thing["move"] = {"help":["id_to_move move_to_id", "moves first id to second id"], "run": lambda args: self.callback_handler.run(UserActionCodes.MOVE_USER, int(args[0]), int(args[1]))}

    def start_input_loop(self):
        self.can_run = True
        self.display_help()
        while self.can_run:
            inp = input()
            cmd = None
            args = list()
            for s in inp.split():
                if len(s):
                    if cmd is None:
                        cmd = s
                    else:
                        args.append(s)
            

            if cmd in self.thing:
                try:
                    self.thing[cmd]["run"](args)
                #except IndexError as e:
                except KeyError as e:
                    self.callback_handler.run(BasicCallCodes.LOG_ERROR, f"Error while trying to run command ({cmd}) with args ({args})  Exception: {e}")
            else:
                print(f"Unrecignizable command {cmd}")
                self.display_help()
    
    def display_help(self):
        for s in self.thing:
            print(f"{s} - {self.thing[s]['help'][0]}")
            if len(self.thing[s]['help']) > 1:
                for ss in self.thing[s]["help"][1:]:
                    print("\t" + ss)

        #print("h              - display this")
        #print('sys "..."      - send system message')
        #print('start ip port  - start server')
        #print('stop           - stop server')
        #print('quit           - quit the program')

    def quit_loop(self):
        self.can_run = False
        self.callback_handler.run(UserActionCodes.STOP_SERVER)