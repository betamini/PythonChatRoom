import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import socket_server
import os
kivy.require("1.11.1")

class ConfigPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.getinfogrid = GridLayout(cols=2)

        if os.path.isfile("prev_conf.txt"):
            with open("prev_conf.txt", "r") as f:
                prev_ip, prev_port = f.read().split(",")
        else:
            prev_ip = ""
            prev_port = ""

        self.getinfogrid.add_widget(Label(text="IP:"))
        self.ip = TextInput(multiline=False, text=prev_ip)
        self.getinfogrid.add_widget(self.ip)

        self.getinfogrid.add_widget(Label(text="Port:"))
        self.port = TextInput(multiline=False, text=prev_port)
        self.getinfogrid.add_widget(self.port)

        self.add_widget(self.getinfogrid)

        self.join = Button(text="Start Server", size_hint_y=0.25)
        self.join.bind(on_press=self.joinButton)
        self.add_widget(self.join)

    def joinButton(self, instance):
        ip = self.ip.text
        port = self.port.text

        print(f"Attempting to open server with {ip}:{port}")

        with open("prev_conf.txt", "w") as f:
            f.write(f"{ip},{port}")

        info = f"Attempting to open server with {ip}:{port}"
        server_ui.info_page.update_info(info)
        server_ui.screen_manager.current = "Info"
        Clock.schedule_once(self.start_server, 0.2)
    
    def start_server(self, _):
        ip = self.ip.text
        port = int(self.port.text)

        server_ui.consol_page.start_server(ip, port)

        server_ui.screen_manager.current = "Consol"

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

class ConsolPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1
        self.placeholder = Label(text="!Server!", halign="center", valign="middle", font_size=30)
        self.add_widget(self.placeholder)
    
    def start_server(self, ip, port):
        self.run_state = True
        socket_server.start_server(ip, port, ErrorHandler.show_error, self.should_run_callable)

    def should_run_callable(self):
        return self.run_state


class server_ui(App):
    def build(self):
        self.error_handler = ErrorHandler()
        self.screen_manager = ScreenManager()

        self.connect_page = ConfigPage()
        screen = Screen(name="Config")
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        self.info_page = InfoPage()
        screen = Screen(name="Info")
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        self.consol_page = ConsolPage()
        screen = Screen(name="Consol")
        screen.add_widget(self.consol_page)
        self.screen_manager.add_widget(screen)


        return self.screen_manager

class ErrorHandler:  
    def show_error(self, error_msg):
        server_ui.chat_page.run_state = False
        self.countdown = 5
        self.error_msg = error_msg
        self.updateclockthing = Clock.schedule_interval(self.show_error_update_text, 1)
        server_ui.screen_manager.current = "Info"
        Clock.schedule_once(self.show_error_connect_proxy, 5.5)

    def show_error_update_text(self, _):
        server_ui.info_page.update_info(self.error_msg + f"\nReturning to Front page in {self.countdown}")
        self.countdown -= 1
        if self.countdown <= 0:
            return False
    
    def show_error_connect_proxy(self, _):
        server_ui.screen_manager.current = "Config"
    

if __name__ == "__main__":
    server_ui = server_ui()
    server_ui.run()