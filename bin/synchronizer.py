# Synchronizer

# Import libraries
import os
import numpy as np
import easygui
import pyxdf
import pandas as pd

# Base paths
DIR_ROOT      = os.path.dirname(os.path.abspath(''))
DIR_DATA      = os.path.join(DIR_ROOT, "data")
DIR_SYNC      = os.path.join(DIR_DATA, "synchronized")
DIR_EEG       = os.path.join(DIR_DATA, "eeg")
DIR_VIDEO     = os.path.join(DIR_DATA, "video")
DIR_SIMULATOR = os.path.join(DIR_DATA, "sim")

# Get list of files to synchronize
eeg_files   = [file for file in os.listdir(DIR_EEG) if file.endswith(".xdf")]
sim_files   = [file for file in os.listdir(DIR_SIMULATOR) if file.endswith(".dat")]

# Display a choicebox to select the xdf file
file_eeg        = os.path.join(DIR_EEG, easygui.choicebox("Select the EEG file to synchronize", "Synchronize", eeg_files))
file_simulator  = os.path.join(DIR_SIMULATOR, easygui.choicebox("Select the driving simulator file to synchronize", "Synchronize", sim_files))
file_sim_events = os.path.join(DIR_SIMULATOR, os.path.splitext(os.path.basename(file_simulator))[0] + ".evt")

# Check if file_sim_events exists, if not, display an error
if not os.path.exists(file_sim_events):
    easygui.msgbox("Event file not found. Please check the file name and try again.", "Error")
    exit()

trigger_time = float(easygui.enterbox(msg="Enter trigger audio time (in seconds)", title="Trigger time", default = ""))

# Read EEG data
streams, header = pyxdf.load_xdf(file_eeg)

# Separate video and EEG data streams
video_raw_data = streams[0]

video_time_stamps = video_raw_data["time_stamps"]
true_video_start  = float(video_raw_data["footer"]["info"]["first_timestamp"][0])
true_video_end    = float(video_raw_data["footer"]["info"]["last_timestamp"][0])

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
eeg_sync_data["time_stamp"] = eeg_sync_data["time_stamp"] - eeg_sync_time_stamp

# Read simulator data
sim_data = pd.read_csv(file_simulator, sep=" ")
event_data = pd.read_csv(file_sim_events, sep="\s+|#", engine="python")

# Get trigger time from event data
sim_trigger_time = event_data[event_data["Event_Name"].str.contains("ReferencePoint")]["startTime"].values[0]
sim_trigger_index = np.argmin(np.abs(sim_data["SimTime"] - sim_trigger_time))

sim_sync_data = sim_data.iloc[sim_trigger_index:]
sim_sync_data["time_stamp"] = sim_sync_data["SimTime"] - sim_trigger_time

# Export synced data
experiment_basename = os.path.splitext(os.path.basename(file_eeg))[0]

eeg_sync_data.to_csv(os.path.join(DIR_SYNC, experiment_basename + "_eeg_sync.csv"), index=False)
sim_sync_data.to_csv(os.path.join(DIR_SYNC, experiment_basename + "_sim_sync.csv"), index=False)




