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
import easygui
import pyxdf
import pandas as pd

def sync_eeg_data(trigger_time, eeg_file = None):
    # If eeg_file is not provided or empty, prompt user to select one using GUI
    if not eeg_file:
        # Select the EEG folder
        dir_eeg   = easygui.diropenbox(title = "Select EEG folder")
        eeg_files = [file for file in os.listdir(dir_eeg) if file.endswith(".xdf")]
        
        # Display a choicebox to select the xdf file
        eeg_file = os.path.join(dir_eeg, easygui.choicebox("Select the EEG file to synchronize", "EEG Data", eeg_files))

    # Read EEG data
    streams, header = pyxdf.load_xdf(eeg_file)

    # Separate video and EEG data streams
    video_raw_data = streams[0]

    video_time_stamps = video_raw_data["time_stamps"]
    true_video_start  = float(video_raw_data["footer"]["info"]["first_timestamp"][0])
    
    true_video_time_stamps   = video_time_stamps - true_video_start
    vide_trigger_index       = np.argmin(np.abs(true_video_time_stamps - trigger_time))
    video_trigger_time_stamp = video_time_stamps[vide_trigger_index]

    # Get EEG data stream
    eeg_raw_data = streams[2]

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
