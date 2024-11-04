# Synchronize EEG data
# Author: Ramiro Reyes
# Date: 2023-09-01
# License: MIT License
#
# Description: This script synchronizes EEG data with video data.
# It uses the trigger time from the EEG video to find the closest time stamp in the EEG data.
# It returns a pandas dataframe with the EEG data and corrected time stamps.

# Import libraries
import os
import numpy as np
import pyxdf
import pandas as pd
import tkinter as tk
from tkinter import filedialog

def sync_eeg_data(trigger_time, eeg_file = None):

    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.lift()      # Bring the main window to the foreground
    root.attributes('-topmost', True)  # Make sure the window remains on top

    # If eeg_file is not provided or empty, prompt user to select one using GUI

    if not eeg_file:
        # Prompt user to select EEG folder using tkinter
        dir_eeg = filedialog.askdirectory(title="Select EEG folder")
        if not dir_eeg:
            root.destroy()
            return None
        eeg_files = [file for file in os.listdir(dir_eeg) if file.endswith(".xdf")]

        # Prompt user to select the xdf file using tkinter
        eeg_file = filedialog.askopenfilename(title="Select the EEG file to synchronize", initialdir=dir_eeg, filetypes=[("XDF files", "*.xdf")])
        if not eeg_file:
            root.destroy()
            return None

    root.destroy()  # Close the root window once we're done

    # Read EEG data
    streams, header = pyxdf.load_xdf(eeg_file)

    # Separate video and EEG data streams
    video_raw_data = next((stream for stream in streams if stream['info']['type'] == ['video']), None)

    video_time_stamps = video_raw_data["time_stamps"]
    true_video_start  = float(video_raw_data["footer"]["info"]["first_timestamp"][0])
    
    true_video_time_stamps   = video_time_stamps - true_video_start
    vide_trigger_index       = np.argmin(np.abs(true_video_time_stamps - trigger_time))
    video_trigger_time_stamp = video_time_stamps[vide_trigger_index]

    # Get EEG data stream
    eeg_raw_data = next((stream for stream in streams if stream['info']['type'] == ['EEG']), None)

    # Extract EEG data
    eeg_signal     = eeg_raw_data["time_series"]
    eeg_time_stamp = eeg_raw_data["time_stamps"]

    # Extract channel labels
    channel_info = eeg_raw_data["info"]["desc"][0]["channels"]

    channel_labels = []
    for entry in channel_info:
        for channel in entry['channel']:
            channel_labels.append(channel['label'][0])

    # Create dataframe with channel data
    eeg_data = pd.DataFrame(eeg_signal, columns=channel_labels)

    # Add time stamp column to eeg data
    eeg_data["time_stamp"] = eeg_time_stamp

    # Find the closes eeg_time stamp to the trigger time stamp
    eeg_trigger_index = np.argmin(np.abs(eeg_time_stamp - video_trigger_time_stamp))

    eeg_sync_time_stamp = eeg_time_stamp[eeg_trigger_index]

    # Generate synced eeg data with corrected time stamps
    eeg_sync_data = eeg_data.iloc[eeg_trigger_index:]
    
    eeg_sync_data["sync_time_stamp"] = eeg_sync_data["time_stamp"] - eeg_sync_time_stamp

    return eeg_sync_data
