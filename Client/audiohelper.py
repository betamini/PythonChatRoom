import pyaudio
import time
import threading
from Client.client_controller_util import UserActionCodes, ViewCallCodes

audio = None
callbackhandler = None

def setup(callback_handler, send_audio_function):
    global audio
    global callbackhandler

    callbackhandler = callback_handler
    audio = Audio(send_audio_function)
    #SEND_CHAT_AUDIO = auto() 
    # (stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)
    # (stream_bytes, frame_count_int, time_info_dict, status_enum)
    callbackhandler.register(UserActionCodes.TEST_AUDIO, audio.test_audio)
    callbackhandler.register(UserActionCodes.START_AUDIO, lambda : audio.start_rec_stream())
    callbackhandler.register(UserActionCodes.STOP_AUDIO, lambda : audio.stop_rec_stream())
    callbackhandler.register(ViewCallCodes.NEW_CHAT_AUDIO, lambda  user_str, audiobytes, rate, frame_count, width, channels, chunk, status, time_info:audio.play_stream.write(bytes(audiobytes), frame_count))


def terminate():
    global audio
    global callbackhandler

    callbackhandler.unregister(UserActionCodes.TEST_AUDIO, audio.test_audio)
    callbackhandler.unregister(UserActionCodes.START_AUDIO, lambda : audio.start_rec_stream())
    callbackhandler.unregister(UserActionCodes.STOP_AUDIO, lambda : audio.stop_rec_stream())
    callbackhandler.unregister(ViewCallCodes.NEW_CHAT_AUDIO, lambda  user_str, audiobytes, rate, frame_count, width, channels, chunk, status, time_info:audio.play_stream.write(bytes(audiobytes), frame_count))

    audio.terminate()
    audio = None
    callbackhandler = None

class Audio(pyaudio.PyAudio):
    # callback(in_data, frame_count, time_info, status):
    # callback must return a tuple (None, pyaudio.paContinue)
    def __init__(self, send_audio_function, CHUNK=1024, WIDTH=2, CHANNELS=1, RATE=8000):
        super().__init__()
        self.RATE = RATE
        self.CHUNK = CHUNK
        self.WIDTH = WIDTH
        self.CHANNELS = CHANNELS
        self.send_callback = send_audio_function
        
        self.play_stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK)

        self.record_stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.send_callback_func,
                start=False)

    def start_rec_stream(self):
        if self.record_stream.is_stopped():
            self.record_stream.start_stream()
        callbackhandler.run(ViewCallCodes.UPDATE_AUDIO_STATUS, self.record_stream.is_active())

    def stop_rec_stream(self):
        if self.record_stream.is_active():
            self.record_stream.stop_stream()
        callbackhandler.run(ViewCallCodes.UPDATE_AUDIO_STATUS, self.record_stream.is_active())

    def terminate(self):
        self.close_stream(self.play_stream)
        self.stop_rec_stream()
        self.close_stream(self.record_stream)
        return super().terminate()

    def test_audio(self, timeout):
        stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                output=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self._wire_audio,
                start=True)
        if timeout is not None:
            threading.Timer(timeout, self.close_stream, args=stream).start()

    def _wire_audio(self, in_data, frame_count, time_info, status):
        return (in_data, pyaudio.paContinue)
    
    def close_stream(self, stream):
        stream.stop_stream()
        stream.close()

    # (stream_bytes, frame_count_int, time_info_dict, status_enum)
    def send_callback_func(self, stream_bytes, frame_count_int, time_info_dict, status_enum):
        # (stream_bytes, rate_int, frame_count_int, width_int, channels_int, chunk_size_int, status_enum, time_info_dict)
        self.send_callback(stream_bytes, self.RATE, frame_count_int, self.WIDTH, self.CHANNELS, self.CHUNK, status_enum, time_info_dict)
        return (None, pyaudio.paContinue)