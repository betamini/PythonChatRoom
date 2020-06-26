import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import pyaudio
import socket_client
import os
kivy.require("1.11.1")

class ConnectPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.getinfogrid = GridLayout(cols=2)

        if os.path.isfile("prev_connect.txt"):
            with open("prev_connect.txt", "r", encoding="utf-8") as f:
                try:
                    prev_ip, prev_port, prev_username = f.read().split(",")
                except:
                    prev_ip = ""
                    prev_port = ""
                    prev_username = "" 

        self.getinfogrid.add_widget(Label(text="IP:"))
        self.ip = TextInput(multiline=False, text=prev_ip)
        self.getinfogrid.add_widget(self.ip)

        self.getinfogrid.add_widget(Label(text="Port:"))
        self.port = TextInput(multiline=False, text=prev_port)
        self.getinfogrid.add_widget(self.port)

        self.getinfogrid.add_widget(Label(text="Username:"))
        self.username = TextInput(multiline=False, text=prev_username)
        self.getinfogrid.add_widget(self.username)

        self.add_widget(self.getinfogrid)

        self.join = Button(text="Join", size_hint_y=0.25)
        self.join.bind(on_press=self.joinButton)
        self.add_widget(self.join)
    
    def joinButton(self, instance):
        ip = self.ip.text
        port = self.port.text
        username = self.username.text

        print(f"Attempting to connect to {ip}:{port} as {username}")

        #TODO
        #store in json file format
        with open("prev_connect.txt", "w", encoding="utf-8") as f:
            f.write(f"{ip},{port},{username}")

        info = f"Attempting to connect to {ip}:{port} as {username}"
        myapp.info_page.update_info(info)
        myapp.screen_manager.current = "Info"
        Clock.schedule_once(self.connect, 0.2)
    
    def connect(self, _):
        ip = self.ip.text
        port = int(self.port.text)
        username = self.username.text

        if not socket_client.connect(ip, port, username, myapp.error_handler.show_error):
            return

        myapp.chat_page.start_listening()

        myapp.screen_manager.current = "Chat"
        
# This class is an improved version of Label
# Kivy does not provide scrollable label, so we need to create one
class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        # Now we need two wodgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Methos called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at teh bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        # As we are updating above, text height, so also label and layout height are going to be bigger
        # than the area we have for this widget. ScrollView is going to add a scroll, but won't
        # scroll to the botton, nor there is a method that can do that.
        # That's why we want additional, empty wodget below whole text - just to be able to scroll to it,
        # so scroll to the bottom of the layout
        self.scroll_to(self.scroll_to_point)

class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_state = False

        self.cols = 1
        self.rows = 2

        self.history = ScrollableLabel(size_hint_y=9)
        self.add_widget(self.history)

        
        bottom_line = GridLayout(cols=2)

        self.new_message = TextInput(size_hint_x=4, multiline=False)
        bottom_line.add_widget(self.new_message)
        
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)
        bottom_line.add_widget(self.send)

        self.add_widget(bottom_line)

    def start_listening(self):
        self.run_state = True
        socket_client.start_listening(self.incoming_message_callback, myapp.error_handler.show_error, self.should_run_callable)

    def should_run_callable(self):
        return self.run_state

    def incoming_message_callback(self, username, message, msg_type):
        if msg_type == "sys_msg_dist":
            self.history.update_chat_history(f"[color=00ff00]{message}[/color]")
        elif msg_type == "chat_msg_dist":
            self.history.update_chat_history(f"[color=8080ff]{username}[/color] > {message}")
    
    def send_message(self, _):
        message = self.new_message.text
        self.new_message.text = ""

        if message:
            self.history.update_chat_history(f"{myapp.connect_page.username.text} > {message}")
            #self.history.update_chat_history(f"[color=dd2020]{myapp.connect_page.username.text}[/color] > {message}")
            socket_client.send_chat_msg(message)

        

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


        return self.screen_manager

class ErrorHandler:  
    def show_error(self, error_msg):
        myapp.chat_page.run_state = False
        self.countdown = 5
        self.error_msg = error_msg
        self.updateclockthing = Clock.schedule_interval(self.show_error_update_text, 1)
        myapp.screen_manager.current = "Info"
        Clock.schedule_once(self.show_error_connect_proxy, 5.5)

    def show_error_update_text(self, _):
        myapp.info_page.update_info(self.error_msg + f"\nReturning to Front page in {self.countdown}")
        self.countdown -= 1
        if self.countdown <= 0:
            return False
    
    def show_error_connect_proxy(self, _):
        myapp.screen_manager.current = "Connect"
    

if __name__ == "__main__":
    myapp = MyApp()
    myapp.run()