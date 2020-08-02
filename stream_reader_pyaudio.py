import numpy as np
import pyaudio
import time, sys, math
from collections import deque

from utils import *

class Stream_Reader:
    def __init__(self, device = None, rate = None, updates_per_second = 1000, FFT_window_size = None):

        self.rate = rate
        self.pa = pyaudio.PyAudio()

        self.update_window_n_frames = 1024
        self.data_buffer = None

        self.device = device
        if self.device is None:
            self.device = self.input_device()
        if self.rate is None:
            self.rate = self.valid_low_rate(self.device)

        self.update_window_n_frames = round_up_to_even(self.rate / updates_per_second)
        self.updates_per_second = self.rate / self.update_window_n_frames
        self.info = self.pa.get_device_info_by_index(self.device)
        self.data_capture_delays = deque(maxlen = 20)
        self.new_data = False

        self.stream = self.pa.open(format = pyaudio.paInt16, channels = 1, rate = self.rate,input = True, frames_per_buffer = self.update_window_n_frames,stream_callback = self.non_blocking_stream_read)

    def non_blocking_stream_read(self, in_data, frame_count, time_info, status):
        if self.data_buffer is not None:
            self.data_buffer.append_data(np.frombuffer(in_data, dtype=np.int16))
            self.new_data = True

        return in_data, pyaudio.paContinue

    def stream_start(self, data_windows_to_buffer = None):
        self.data_windows_to_buffer = data_windows_to_buffer

        if data_windows_to_buffer is None:
            self.data_windows_to_buffer = int(self.updates_per_second / 2)
        else:
            self.data_windows_to_buffer = data_windows_to_buffer

        self.data_buffer = numpy_data_buffer(self.data_windows_to_buffer, self.update_window_n_frames)

        self.stream.start_stream()
        self.stream_start_time = time.time()

    def terminate(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def valid_low_rate(self, device, test_rates = [44100, 22050]):
        for testrate in test_rates:
            if self.test_device(device, rate=testrate):
                return testrate

        self.info = self.pa.get_device_info_by_index(device)
        default_rate = int(self.info["defaultSampleRate"])

        if self.test_device(device, rate = default_rate):
            return default_rate
            
        return default_rate

    def test_device(self, device, rate = None):
        try:
            self.info = self.pa.get_device_info_by_index(device)
            if not self.info["maxInputChannels"] > 0:
                return False

            if rate is None:
                rate = int(self.info["defaultSampleRate"])

            stream = self.pa.open(format = pyaudio.paInt16, channels = 1, input_device_index = device, frames_per_buffer = self.update_window_n_frames, rate = rate, input = True)
            stream.close()
            return True
        except Exception:
            return False

    def input_device(self):
        mics = []
        for device in range(self.pa.get_device_count()):
            if self.test_device(device):
                mics.append(device)

        if len(mics) == 0:
            sys.exit(0)

        return mics[0]