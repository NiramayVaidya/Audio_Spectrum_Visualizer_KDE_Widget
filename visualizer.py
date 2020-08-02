import numpy as np
import time, sys, math
import pygame

from collections import deque
from matplotlib import cm

class Spectrum_Visualizer:
    def __init__(self, ear):

        self.plot_audio_history = True
        self.ear = ear

        self.HEIGHT = 225
        window_ratio = 2

        self.HEIGHT = round(self.HEIGHT)
        self.WIDTH = round(window_ratio * self.HEIGHT)
        self.y_ext = [round(0.05 * self.HEIGHT), self.HEIGHT]
        self.cm = cm.plasma

        self.toggle_history_mode()

        self.add_slow_bars = 1
        self.add_fast_bars = 1
        self.slow_bar_thickness = max(0.00002 * self.HEIGHT, 1.25 / self.ear.n_frequency_bins)

        self.fast_bar_colors = [list((255 * np.array(self.cm(i))[:3]).astype(int)) for i in np.linspace(0, 255, self.ear.n_frequency_bins).astype(int)]
        self.slow_bar_colors = [list(np.clip((255 * 3.5 * np.array(self.cm(i))[:3]).astype(int) , 0, 255)) for i in np.linspace(0, 255, self.ear.n_frequency_bins).astype(int)]
        self.fast_bar_colors = self.fast_bar_colors[::-1]
        self.slow_bar_colors = self.slow_bar_colors[::-1]

        self.slow_features = [0] * self.ear.n_frequency_bins
        self.frequency_bin_max_energies = np.zeros(self.ear.n_frequency_bins)
        self.frequency_bin_energies = self.ear.frequency_bin_energies
        self.bin_text_tags, self.bin_rectangles = [], []

        self.start_time = None
        self.vis_steps = 0
        self.fps_interval = 10
        self.fps = 0
        self._is_running = False

    def toggle_history_mode(self):
        if self.plot_audio_history:
            self.bg_color = 10
            self.decay_speed = 0.10
            self.inter_bar_distance = 0            
            self.avg_energy_height = 0.1125
            self.alpha_multiplier = 0.995
            self.move_fraction = 0.015
            self.shrink_f = 0.994
        else:
            self.bg_color = 60
            self.decay_speed = 0.06
            self.inter_bar_distance = int(0.2 * self.WIDTH / self.ear.n_frequency_bins)
            self.avg_energy_height = 0.225

        self.bar_width = (self.WIDTH / self.ear.n_frequency_bins) - self.inter_bar_distance

        self.slow_bars, self.fast_bars, self.bar_x_positions = [],[],[]
        for i in range(self.ear.n_frequency_bins):
            x = int(i * self.WIDTH / self.ear.n_frequency_bins)
            fast_bar = [int(x), 0, math.ceil(self.bar_width), None]
            slow_bar = [int(x), None, math.ceil(self.bar_width), None]
            self.bar_x_positions.append(x)
            self.fast_bars.append(fast_bar)
            self.slow_bars.append(slow_bar)

    def start(self):
        pygame.display.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.NOFRAME)
        self.screen.fill((self.bg_color, self.bg_color, self.bg_color))

        if self.plot_audio_history:
            self.screen.set_alpha(255)
            self.prev_screen = self.screen

        self._is_running = True

    def stop(self):
        del self.screen
        del self.prev_screen
        pygame.display.quit()
        self._is_running = False

    def update(self):
        if np.min(self.ear.bin_mean_values) > 0:
            self.frequency_bin_energies = self.avg_energy_height * self.ear.frequency_bin_energies / self.ear.bin_mean_values
        
        if self.plot_audio_history:
            new_w, new_h = int((2 + self.shrink_f) / 3 * self.WIDTH), int(self.shrink_f * self.HEIGHT)

            prev_screen = pygame.transform.scale(self.prev_screen, (new_w, new_h))

        self.screen.fill((self.bg_color, self.bg_color, self.bg_color))

        if self.plot_audio_history:
            new_pos = int(self.move_fraction * self.WIDTH - (0.0133 * self.WIDTH)), int(self.move_fraction * self.HEIGHT)
            self.screen.blit(pygame.transform.rotate(prev_screen, 180), new_pos)

        if self.start_time is None:
           self.start_time = time.time() 

        self.vis_steps += 1

        if self.vis_steps % self.fps_interval == 0:
            self.fps = self.fps_interval / (time.time() - self.start_time)
            self.start_time = time.time()
        
        self.plot_bars()

        pygame.display.flip()

    def plot_bars(self):
        new_slow_features = []
        local_height = self.y_ext[1] - self.y_ext[0]
        feature_values = self.frequency_bin_energies[::-1]

        for i in range(len(self.frequency_bin_energies)):
            feature_value = feature_values[i] * local_height

            self.fast_bars[i][3] = int(feature_value)

            if self.plot_audio_history:
                self.fast_bars[i][3] = int(feature_value + 0.02 * self.HEIGHT)

            if self.add_slow_bars:
                self.decay = min(0.99, 1 - max(0,self.decay_speed * 60 / self.ear.fft_fps))
                slow_feature_value = max(self.slow_features[i] * self.decay, feature_value)
                new_slow_features.append(slow_feature_value)
                self.slow_bars[i][1] = int(self.fast_bars[i][1] + slow_feature_value)
                self.slow_bars[i][3] = int(self.slow_bar_thickness * local_height)

        if self.add_fast_bars:     
            for i, fast_bar in enumerate(self.fast_bars):
                pygame.draw.rect(self.screen, self.fast_bar_colors[i], fast_bar, 0)

        if self.plot_audio_history:
                self.prev_screen = self.screen.copy()
                self.prev_screen = pygame.transform.rotate(self.prev_screen, 180)
                self.prev_screen.set_alpha(self.prev_screen.get_alpha() * self.alpha_multiplier)

        if self.add_slow_bars: 
            for i, slow_bar in enumerate(self.slow_bars):
                pygame.draw.rect(self.screen, self.slow_bar_colors[i], slow_bar, 0)
                
        self.slow_features = new_slow_features

        self.screen.blit(pygame.transform.rotate(self.screen, 180), (0, 0))