import time
import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'HIDE'
os.environ['SDL_VIDEO_WINDOW_POS'] = '900,500'
from pygame.locals import *

from stream_analyzer import Stream_Analyzer
from utils import *

ear = Stream_Analyzer(device = None, rate = None, FFT_window_size_ms = 60, updates_per_second = 1000, smoothing_length_ms = 50, n_frequency_bins = 400)

fps = 60
last_update = time.time()
try:
    while True:
        if (time.time() - last_update) > (1.0 / fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                move_window()
except KeyboardInterrupt:
    ear.stream_reader.terminate()
    sys.exit(0)