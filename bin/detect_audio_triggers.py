# Detect Audio Triggers
# Author: Ramiro Reyes
# Date: 2023-09-01
# License: MIT License

# Description: This script detects audio triggers in a video file. 
# It uses a spectrogram to visualize the audio and allows the user to select the trigger time. 
# The trigger time is returned as a float.

# Import libraries
import sys
import numpy as np
import easygui
import librosa
import librosa.display
import moviepy.editor as mp
from scipy.signal import find_peaks
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QListWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.signal import find_peaks

class SpectrogramWindow(QMainWindow):
    def __init__(self, y, sr, segment_length = 15, hz_target = 9000):
        super().__init__()

        # Set up the variables
        self.y               = y
        self.sr              = sr
        self.segment_length  = segment_length
        self.hz_target       = hz_target
        self.current_segment = 0
        self.trigger_time    = None
        
        # Set up the GUI layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        layout = QVBoxLayout(self.main_widget)

        # Matplotlib setup
        self.canvas = FigureCanvas(Figure(figsize=(8, 6)))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.subplots()

        # List for peak times
        self.peak_list = QListWidget(self)
        self.peak_list.itemClicked.connect(self.select_peak)
        layout.addWidget(self.peak_list)

        # Navigation buttons
        self.prev_button = QPushButton("Previous Segment")
        self.prev_button.clicked.connect(self.prev_segment)
        layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next Segment")
        self.next_button.clicked.connect(self.next_segment)
        layout.addWidget(self.next_button)

        # Initial plot
        self.update_plot()

    def select_peak(self):
        selected_time = self.peak_list.currentItem().text()
        self.trigger_time = float(selected_time.split()[0])
        self.close() # Close the GUI
        
    def next_segment(self):
        self.current_segment += 1
        self.update_plot()

    def prev_segment(self):
        self.current_segment = max(0, self.current_segment - 1)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.peak_list.clear()

        start_sample = self.current_segment * self.segment_length * self.sr
        end_sample   = start_sample + self.segment_length * self.sr
        y_segment    = self.y[start_sample:end_sample]

        D = librosa.stft(y_segment)
        magnitude, _ = librosa.magphase(D)
        magnitude_db = librosa.amplitude_to_db(magnitude)

        # Find peaks for the segment
        frequency_bins  = librosa.core.fft_frequencies(sr=self.sr)
        bin_target      = np.argmin(np.abs(frequency_bins - self.hz_target))
        magnitude_line  = magnitude[bin_target]
        peak_indices, _ = find_peaks(magnitude_line, prominence=0.1)
        
        # Adjust peak times to account for the cumulative time
        peak_times_segment = librosa.core.frames_to_time(peak_indices, sr=self.sr) + self.current_segment * self.segment_length

        # Add peaks to the list
        for time in peak_times_segment:
            self.peak_list.addItem(f"{time:.2f} s")

        # Plot
        librosa.display.specshow(magnitude_db, sr=self.sr, x_axis='time', y_axis='linear', cmap='viridis', ax=self.ax)
        
        # Adjusting the plot's x-axis
        x_ticks = self.ax.get_xticks()
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels([f"{tick + self.current_segment * self.segment_length:.2f}" for tick in x_ticks])
        
        # Plotting the peaks
        self.ax.scatter(peak_times_segment - self.current_segment * self.segment_length, [self.hz_target] * len(peak_times_segment), color='red', marker='x')
        self.ax.set_title(f'Spectrogram Segment {self.current_segment + 1} with Peaks at ~{self.hz_target} Hz')

        self.canvas.draw()

# Extract audio samples directly to a numpy array and get the sampling rate
def detect_audio_triggers(video_path=None, segment_length=15, hz_target=9000):
    if video_path is None:
        video_path = easygui.fileopenbox(default='*.mp4', filetypes=["*.mp4"], title="Select an MP4 video file")
        if not video_path:  # If the user cancels the file dialog
            return

    audio = mp.AudioFileClip(video_path)
    y = audio.to_soundarray(fps=22050, nbytes=2).mean(axis=1)  # Average over the two channels to get mono
    sr = 22050  # Setting the sampling rate to 22050 to match the fps value for the audio
    
    try:
        app = QApplication(sys.argv)
        main = SpectrogramWindow(y, sr, segment_length=segment_length, hz_target=hz_target)
        main.show()
        app.exec_()
        
        # Print and return the trigger_time
        print(f"Selected peak time: {main.trigger_time} seconds")
        return main.trigger_time    

    except SystemExit:
        pass

detect_audio_triggers(segment_length=5, hz_target=9000)
