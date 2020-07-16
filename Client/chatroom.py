import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import escape_markup
from callback_handler import BasicCallCodes
from Client.client_controller_util import ViewCallCodes, UserActionCodes
import socket_util
import functools
import os
kivy.require("1.11.1")

class ConnectPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.getinfogrid = GridLayout(cols=2)

        prev_ip = ""
        prev_port = ""
        prev_username = "" 
        if os.path.isfile("prev_connect.txt"):
            with open("prev_connect.txt", "r", encoding="utf-8") as f:
                try:
                    prev_ip, prev_port, prev_username = f.read().split(",")
                except:
                    pass

        self.getinfogrid.add_widget(Label(text="IP:"))
        self.ip = MyTextInput(multiline=False, text=prev_ip)
        self.getinfogrid.add_widget(self.ip)
        self.ip.enter_function = lambda *args: callback_handler.run(UserActionCodes.JOIN, self.ip.text, int(self.port.text))

        self.getinfogrid.add_widget(Label(text="Port:"))
        self.port = MyTextInput(multiline=False, text=prev_port)
        self.getinfogrid.add_widget(self.port)
        self.port.enter_function = lambda *args: callback_handler.run(UserActionCodes.JOIN, self.ip.text, int(self.port.text))

        self.getinfogrid.add_widget(Label(text="Username:"))
        #self.username = TextInput(multiline=False, text=prev_username)
        self.username = MyTextInput(multiline=False, text=prev_username)
        self.username.enter_function = lambda *args: callback_handler.run(UserActionCodes.JOIN, self.ip.text, int(self.port.text))
        #temp = self.username.keyboard_on_key_down
        #self.username.keyboard_on_key_down = lambda window, keycode, text, modifiers: print(f"Window: {window}  Keycode: {keycode}  Text: {text}  Modifiers: {modifiers}  Ingnore this: {temp(window, keycode, text, modifiers)}")
        self.getinfogrid.add_widget(self.username)

        self.add_widget(self.getinfogrid)

        self.join = Button(text="Join", size_hint_y=0.25)
        self.join.bind(on_press= lambda _: callback_handler.run(UserActionCodes.JOIN, self.ip.text, int(self.port.text))) #myapp.connect_page.ip.text
        self.add_widget(self.join)

        self.test_audio = Button(text="Test audio", size_hint_y=0.25)
        self.test_audio.bind(on_press= lambda _: callback_handler.run(UserActionCodes.TEST_AUDIO, 4))
        self.add_widget(self.test_audio)
    
    def save_ip_port_and_name(self, ip, port):
        #TODO - store in json file format
        with open("prev_connect.txt", "w", encoding="utf-8") as f:
            f.write(f"{ip},{port},{myapp.connect_page.username.text}")

    #def joinButton(self, instance):
    #    ip = self.ip.text
    #    port = self.port.text
    #    username = self.username.text
    #    print(f"Attempting to connect to {ip}:{port} as {username}")


    #    info = f"Attempting to connect to {ip}:{port} as {username}"
    #    myapp.info_page.update_info(info)
    #    myapp.screen_manager.current = "Info"
    #    Clock.schedule_once(self.connect, 0.4)
    
    #def connect(self, _):
    #    ip = self.ip.text
    #    port = int(self.port.text)
    #    username = self.username.text

    #    if callback_handler.run(UserActionCodes.JOIN, (ip, port)):
    #        myapp.screen_manager.current = "Chat"
    #        callback_handler.run(UserActionCodes.SET_USERNAME, username)
    #    else:
    #        myapp.error_handler.show_error("Unable to connect with server")

class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enter_function = None

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print(f"Window: {window}  Keycode: {keycode}  Text: {text}  Modifiers: {modifiers}")
        if keycode[1] == "backspace" and "ctrl" in modifiers:
            last_space = self.text.rfind(" ", 0, self.cursor_index()) + 1
            new_str = self.text[:last_space].strip() + self.text[self.cursor_index():]
            self.text = new_str.strip()
        if keycode[1] == "enter" and self.enter_function != None:
            self.enter_function(modifiers)
        else:
            super().keyboard_on_key_down(window, keycode, text, modifiers)

# This class is an improved version of Label
# Kivy does not provide scrollable label, so we need to create one
class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None, height=0)
        #self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

        # Now we need two wodgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        #self.content = Label(size_hint_y=None, markup=True, font_context="./Client", font_name="unifont-13.0.03")
        #self.content = Label(size_hint_y=None, markup=True)
        self.content = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        self.content.bind(texture_size=lambda label_self, size: f"{self.content.setter('height')(label_self, size[1])} and {self.layout.setter('height')(label_self, size[1])}")
        #self.content.bind(texture_size=lambda label_self, size: print(f"{label_self}, {size}"))

        # We add them to our layout
        self.layout.add_widget(self.content)
        self.layout.add_widget(self.scroll_to_point)

    def add_text_row(self, message, trusted_string=False):
        if not trusted_string:
            message = escape_markup(message)

        if len(self.content.text):
            self.content.text += '\n'
        
        self.content.text += message
        
        self.content.text_size = (self.content.width * 0.97, None)
        #self.content.texture_update()
        #self.content.height = self.content.texture_size[1]
        #self.layout.height = self.content.texture_size[1] + 10

        self.scroll_to(self.scroll_to_point)
    
    def clear_content(self):
        self.content.text = ""

        self.content.text_size = (self.content.width * 0.97, None)
        self.content.texture_update()
        self.content.height = self.content.texture_size[1]
        self.layout.height = self.content.texture_size[1] + 10
        
        self.scroll_to(self.scroll_to_point)

class ChatPage(GridLayout):
    same_room_color = "00cc00"
    sub_room_color = "ff6600"
    #distant_room_color = "00ffcc"
    distant_room_color = "8c8c8c"
    self_user_color = "ffffff"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_audio_stream = False
        self.users = set()
        self.can_listen = set()
        self.can_speak = set()
        self.structure = list()

        self.cols = 1

        self.topgrid = GridLayout(cols=2, rows=1, size_hint_y=9)
        self.history = ScrollableLabel()
        self.users_list = ScrollableLabel()
        self.topgrid.add_widget(self.history)
        self.topgrid.add_widget(self.users_list)
        self.add_widget(self.topgrid)
        
        self.bottom_line = GridLayout(cols=1)

        self.new_message = MyTextInput(size_hint_x=3, multiline=True, hint_text="Enter text here")
        self.bottom_line.add_widget(self.new_message)
        self.new_message.enter_function = lambda *args: self.on_text_input_enter(*args)
        
        #self.send = Button(text="Send")
        #self.send.bind(on_press=lambda *args: self.send_message(self.get_str_from_input_field()))
        #self.bottom_line.add_widget(self.send)

        #self.set_username_button = Button(text="Set name")
        #self.set_username_button.bind(on_press=self.set_username_trigger)
        #self.bottom_line.add_widget(self.set_username_button)

        self.add_widget(self.bottom_line)

        self.helplabel = Label(text="Enter => Send message\nEnter + Alt => Exit Room    Enter + Ctrl => Talk Request    Enter + Shift => Set Username", halign="center")
        self.add_widget(self.helplabel)

        self.pushtotalk = Button(text="Press to activate  (Microphone is off)")
        self.pushtotalk.bind(state=self.push_to_talk)
        self.add_widget(self.pushtotalk)

        self.exit_button = Button(text="Exit")
        self.exit_button.bind(on_press=lambda _:callback_handler.run(UserActionCodes.EXIT_SERVER))
        self.add_widget(self.exit_button)

    def on_text_input_enter(self, modifiers):
        done_something = False
        input_field_str = self.get_str_from_input_field()
        if "ctrl" in modifiers:
            done_something = True
            self.send_talk_request(input_field_str)
        if "alt" in modifiers:
            done_something = True
            self.send_exit_room()
        if "shift" in modifiers:
            done_something = True
            self.set_username(input_field_str)

        if not done_something:
            self.send_message(input_field_str)

    def get_str_from_input_field(self):
        string = self.new_message.text
        self.new_message.text = ""

        return string

    def push_to_talk(self, instance, value):
        #print("my current state is {}".format(value))
        
        if value is "down":
            if self.active_audio_stream:
                callback_handler.run(UserActionCodes.STOP_AUDIO)
                self.active_audio_stream = False
            else:
                self.active_audio_stream = True
                callback_handler.run(UserActionCodes.START_AUDIO)
        #elif value is "normal":
        #    callback_handler.run(UserActionCodes.STOP_AUDIO)
    
    def update_audio_status(self, status_bool):
        self.active_audio_stream = status_bool
        if status_bool:
            status_str = "Press to deactivate (Microphone is on)"
        else:
            status_str = "Press to activate  (Microphone is off)"
        self.pushtotalk.text = status_str
    
    def set_username_trigger(self, _):
        self.set_username(self.get_str_from_input_field())

    def set_username(self, name_str):
        if isinstance(name_str, str):
            if name_str != "":
                myapp.connect_page.username.text = name_str
                callback_handler.run(UserActionCodes.SET_USERNAME, name_str)
    
    def send_message(self, message_str):
        if message_str:
            self.history.add_text_row(f"{self.format_name(myapp.connect_page.username.text)}> {escape_markup(message_str)}", True)
            #self.history.add_text_row(f"[color=dd2020]{myapp.connect_page.username.text}[/color] > {message}")
            callback_handler.run(UserActionCodes.SEND_MSG, message_str)
    
    def new_chat_msg(self, user_str, message_str):
        self.history.add_text_row(f"{self.format_name(user_str)}> {escape_markup(message_str)}", True)

    def format_name(self, user_str):
        if user_str == myapp.connect_page.username.text:
            color = ChatPage.self_user_color
        elif user_str in self.can_listen:
            if user_str in self.can_speak:
                color = ChatPage.same_room_color
            else:
                color = ChatPage.sub_room_color
        else:
            color = ChatPage.distant_room_color
        return f"[b][color={color}]" + escape_markup(user_str) + "[/color][/b]"

    def format_name_color(self, user_str):
        if user_str == myapp.connect_page.username.text:
            color = ChatPage.self_user_color
        elif user_str in self.can_listen:
            if user_str in self.can_speak:
                color = ChatPage.same_room_color
            else:
                color = ChatPage.sub_room_color
        else:
            color = ChatPage.distant_room_color
        return color

    def send_talk_request(self, person_str):
        callback_handler.run(UserActionCodes.SEND_TALK_REQUEST, person_str)
    
    def send_exit_room(self):
        callback_handler.run(UserActionCodes.EXIT_ROOM)

    def update_users_all(self, users_list, can_listen, can_speak, structure):
        self.users_list.clear_content()
        if can_speak != None:
            self.can_speak = set(can_speak)
        if can_listen != None:
            self.can_listen = list(can_listen)
        if users_list != None:
            self.users = set(users_list)
        if structure != None:
            self.structure = structure

        #❔🗣👂
        self.users_list.add_text_row(f"[b]([color={ChatPage.same_room_color}]Same Room[/color], [color={ChatPage.sub_room_color}]Subroom[/color], [color={ChatPage.distant_room_color}]Other Room[/color]) [/b]\n", True)
        self.users_list.add_text_row(f"[b]Can hear you", True)
        for user in self.can_listen:
            self.users_list.add_text_row(self.format_name(str(user)), True)

        #self.users_list.add_text_row("\n[b]Eavesdroppers[/b]", True)
        #for user in self.can_listen - self.can_speak:
        #    self.users_list.add_text_row(self.format_name(str(user)), True)
        #(They can't hear you, but you could be their Eavesdroppe)
        #self.users_list.add_text_row("\n[b]Distant Users[/b]", True)
        #for user in self.users - self.can_listen - self.can_speak:
        #    self.users_list.add_text_row(self.format_name(str(user)), True)
        
        if len(self.structure):
            self.users_list.add_text_row("\n\n[b]Hierarchy[/b]", True)
            self.users_list.add_text_row(self.make_preaty_string(self.structure), True)
            
    def make_preaty_string(self, structure, indent_in="", color_thing=None):
        if color_thing == None:
            color_thing = ChatPage.distant_room_color
        string = ""
        line = "|"
        room_symbol = "v"
        #if level > 1:
        #    indent += (line + " ") * (level - 1)
        for entry in structure:
            #indent = f"[color={self.format_name_color(str(entry))}]" + indent_in + line + " " + "[/color]"
            if not isinstance(entry, list):
                color_thing = self.format_name_color(str(entry))
                if color_thing == ChatPage.self_user_color or color_thing == ChatPage.same_room_color:
                    color_thing = ChatPage.sub_room_color
                string = string + indent_in + self.format_name(str(entry)) + "\n"
            #elif entry != myapp.connect_page.username.text:
            else:
                new_indent = indent_in + f"[color={color_thing}]{line} [/color]"
                #new_indent = f"[color={self.format_name_color(str(entry))}]" + indent_in + line + " " + "[/color]"
                string = string + indent_in + f"[color={color_thing}]{room_symbol}[/color]" + "\n" + self.make_preaty_string(entry, new_indent, color_thing)
        return string

class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.info = Label(halign="center", valign="middle", font_size=30)
        self.info.bind(width=self.update_text_width)
        self.add_widget(self.info)

    def update_info(self, info):
        self.info.text = info
    
    def update_text_width(self, *_):
        self.info.text_size = (self.info.width*0.9, None)


class MyApp(App):
    def build(self):
        self.error_handler = ErrorHandler()
        self.screen_manager = ScreenManager()

        self.connect_page = ConnectPage()
        screen = Screen(name="Connect")
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        self.info_page = InfoPage()
        screen = Screen(name="Info")
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        self.chat_page = ChatPage()
        screen = Screen(name="Chat")
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)

        callback_handler.register(UserActionCodes.JOIN, myapp.connect_page.save_ip_port_and_name)

        callback_handler.register(BasicCallCodes.LOG_DEBUG, lambda msg_str:print(f"DEBUG: {msg_str}"))
        callback_handler.register(BasicCallCodes.LOG_INFO, lambda msg_str:print(f"INFO: {msg_str}"))
        callback_handler.register(BasicCallCodes.LOG_WARNING, lambda msg_str:print(f"WARN: {msg_str}"))
        callback_handler.register(BasicCallCodes.LOG_ERROR, lambda msg_str:print(f"ERROR: {msg_str}"))

        callback_handler.register(ViewCallCodes.NEW_SYS_MSG, lambda message_str:self.chat_page.history.add_text_row(f"[color=00ff00]{escape_markup(message_str)}[/color]", True))
        callback_handler.register(ViewCallCodes.NEW_CHAT_MSG, self.chat_page.new_chat_msg)
        
        callback_handler.register(ViewCallCodes.UPDATE_AUDIO_STATUS, self.chat_page.update_audio_status)
        
        callback_handler.register(ViewCallCodes.UPDATE_USERS_LISTENING, lambda can_listen, can_speak:self.chat_page.update_users_all(None, can_listen, can_speak, None))
        callback_handler.register(ViewCallCodes.UPDATE_USERS_ALL, lambda users_list:self.chat_page.update_users_all(users_list, None, None, None))
        callback_handler.register(ViewCallCodes.UPDATE_USERS_STRUCTURE, lambda structure:self.chat_page.update_users_all(None, None, None, structure))
        
        callback_handler.register(ViewCallCodes.CONNECTION_CLOSED, lambda :self.error_handler.show_error("Connection with server closed"))
        callback_handler.register(ViewCallCodes.CONNECTED_TO_SERVER, lambda :change_screen("Chat"))


        return self.screen_manager

class ErrorHandler:  
    def show_error(self, error_msg):
        self.countdown = 5
        self.error_msg = error_msg
        self.updateclockthing = Clock.schedule_interval(self.show_error_update_text, 1)
        change_screen("Info")
        Clock.schedule_once(lambda _: change_screen("Connect"), 5.5)

    def show_error_update_text(self, _):
        myapp.info_page.update_info(self.error_msg + f"\nReturning to Front page in {self.countdown}")
        self.countdown -= 1
        if self.countdown <= 0:
            return False

def change_screen(name_str):
    global myapp
    myapp.screen_manager.current = name_str
    if name_str == "Chat":
        myapp.chat_page.set_username(myapp.connect_page.username.text)
        myapp.chat_page.history.clear_content()
        myapp.chat_page.users_list.clear_content()

myapp = None
callback_handler = None

def setup(callback_handler_in):
    global myapp
    global callback_handler
    callback_handler = callback_handler_in

    myapp = MyApp()
    myapp.run()

#if __name__ == "__main__":
#    setup()