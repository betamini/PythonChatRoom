# PythonChatRoom

## Dist

### Server

``` PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
& d:/Koding/Prototyping/PythonChatRoom/PythonChatRoom/kivy_venv/Scripts/Activate.ps1
cd D:/Koding/Prototyping/PythonChatRoom/PythonChatRoom/Releases/Server
python -m PyInstaller --name ServerV0 --onefile --clean D:\Koding\Prototyping\PythonChatRoom\PythonChatRoom\Server\server.py --hidden-import=pkg_resources.py2_warn --add-binary='D:\Koding\Prototyping\PythonChatRoom\PythonChatRoom\kivy_venv\share\sdl2\bin\libpng16-16.dll;.'
```

### Client

``` PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
& d:/Koding/Prototyping/PythonChatRoom/PythonChatRoom/kivy_venv/Scripts/Activate.ps1
cd D:/Koding/Prototyping/PythonChatRoom/PythonChatRoom/Releases/Client
python -m PyInstaller --name ChatRoomV0 --onefile --clean D:\Koding\Prototyping\PythonChatRoom\PythonChatRoom\Client\chatroom.py --hidden-import=pkg_resources.py2_warn --add-binary='D:\Koding\Prototyping\PythonChatRoom\PythonChatRoom\kivy_venv\share\sdl2\bin\libpng16-16.dll;.'
```

## Modules

### [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/)

[Wheel file](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

``` PowerShell
pip install D:\Downloads\PyAudio-0.2.11-cp37-cp37m-win_amd64.whl
```

### Kivy

# Tags

## type

### chat_msg_post

From client to server

Tells the server to distribute a message (contents of body) to all other clients (chat_msg_dist)

### chat_msg_dist

From server to client

Distributes chat message (contents of body) to all clients

### sys_msg_dist

From server to client

Distributes system message (contents of body) to all clients

### set_username

sets username to contents of body

## body

## from_user

Specific to chat_msg_dist. Parameter is sett by the server.