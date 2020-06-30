import pyaudio
import time
import threading

class Audio(pyaudio.PyAudio):
    def __init__(self, CHUNK=2048, WIDTH=2, CHANNELS=1, RATE=48000, TEST_RECORD_SECONDS = 6):
        super().__init__()
        self.RATE = RATE
        self.CHUNK = CHUNK
        self.WIDTH = WIDTH
        self.CHANNELS = CHANNELS
        self.TEST_RECORD_SECONDS = TEST_RECORD_SECONDS
        
        self.play_stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK)

    def test_audio(self):
        stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                output=True,
                frames_per_buffer=self.CHUNK)
        print("* recording")

        time.sleep(1)

        for i in range(0, int(self.RATE / self.CHUNK * self.TEST_RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            #pretty_data = ''
            #accum = 0
            #for i in range(0, int(CHUNK/2)):
            #    pretty_data += f"{int.from_bytes(data[i*2:i*2+2], 'big', signed=True)} from {data[i*2:i*2+2]}\n"
            #    accum += int.from_bytes(data[i*2:i*2+2], 'big', signed=True)
            #print(pretty_data)
            #print(int(accum/(CHUNK/2)))
            #out_stream.write(data, CHUNK)
            stream.write(data, self.CHUNK)

        print("* done")

        stream.stop_stream()
        stream.close()

    # callback(in_data, frame_count, time_info, status):
    # callback must return a tuple (None, None)
    def record_to_callback(self, callback, timeout=None):
        stream = self.open(format=self.get_format_from_width(self.WIDTH),
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                #output=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=callback)
        if timeout is not None:
            threading.Timer(timeout, self.terminate_stream, [stream]).start()

        return stream
    
    def terminate_stream(self, stream):
        stream.stop_stream()
        stream.close()

    def simple_stream_wrapper(self, func, in_data, frame_count, time_info, status):
        func(in_data)
        return (None, pyaudio.paContinue)