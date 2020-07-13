from enum import Enum, auto

#(origin_user_str, message_str)
class CallbackHandler(dict):
    def __init__(self, iterable):
        super().__init__(iterable)
        self.add_callcodes(BasicCallCodes)

    def add_callcodes(self, callcodes):
        for e in callcodes:
            self[e] = list()
            
    def register(self, sub_type, function):
        if sub_type in self:
            self[sub_type].append(function)
            debug_str = f"Registered ({function}) to subscribe type ({sub_type})"
            self.run(BasicCallCodes.LOG_DEBUG, debug_str)
            return
        warning_str = f"Unable to register ({function}) to subscribe type ({sub_type}): Subscribe type does not exist"
        print(warning_str)
        self.run(BasicCallCodes.LOG_WARNING, warning_str)
    
    def unregister(self, sub_type, function):
        if sub_type in self:
            if function in self[sub_type]:
                self[sub_type].remove(function)
                return
        warning_str = f"Unable to unregister ({function}) from subscribe type ({sub_type})"
        print(warning_str)
        self.run(BasicCallCodes.LOG_WARNING, warning_str)
    
    def run(self, sub_type, *args):
        if sub_type in self:
            if sub_type not in BasicCallCodes:
                count = 0
                for cb in self[sub_type]:
                    count += 1
                self.run(BasicCallCodes.LOG_DEBUG, f"Running sub_type: ({sub_type}) with args: ({args}) on {count} subscribers")
            
            for cb in self[sub_type]:
                cb(*args)
            return True
        else:
            warning_str = f"Unable to run functions in subscribe type ({sub_type}): Subscribe type does not exist"
            print(warning_str)
            if sub_type != BasicCallCodes.LOG_WARNING:
                self.run(BasicCallCodes.LOG_WARNING, warning_str)
            return False

class BasicCallCodes(Enum):
    LOG_DEBUG = auto() # (string)
    LOG_INFO = auto() # (string)
    LOG_WARNING = auto() # (string)
    LOG_ERROR = auto() # (string)

