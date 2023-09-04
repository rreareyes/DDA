# Synchronize Simulator Data
# Author: Ramiro Reyes
# Date: 2023-09-01
# License: MIT License

# Description: This script synchronizes Simulator data with video data.
# It uses the trigger time from the EEG video to find the closest time stamp in the Simulator data.
# It returns a pandas dataframe with the Simulator data and corrected time stamps.

# Import libraries
import os
import numpy as np
import easygui
import pandas as pd

def sync_simulator_data(trigger_time, sim_file = None):
    # If sim_file is not provided or empty, prompt user to select one using GUI
    if not sim_file:
        # Call a GUI to select the Simulator folder
        dir_simulator = easygui.diropenbox(title = "Select Simulator folder")
        sim_files     = [file for file in os.listdir(dir_simulator) if file.endswith(".dat")]
        
        # Display a choicebox to select the simulator file
        sim_file = os.path.join(dir_simulator, easygui.choicebox("Select the driving simulator file to synchronize", "Simulator Data", sim_files))

    # Grab the event file corresponding to the simulator file
    sim_events_file = os.path.join(os.path.dirname(sim_file), os.path.splitext(os.path.basename(sim_file))[0] + ".evt")

    # Check if file_sim_events exists, if not, display an error
    if not os.path.exists(sim_events_file):
        easygui.msgbox("Event file not found. Please check the file name and try again.", "Error")
        exit()

    # Read simulator data
    sim_data   = pd.read_csv(sim_file, sep=" ")
    event_data = pd.read_csv(sim_events_file, sep="\s+|#", engine="python")

    # Get trigger time from event data
    sim_trigger_time  = event_data[event_data["Event_Name"].str.contains("ReferencePoint")]["startTime"].values[0]
    sim_trigger_index = np.argmin(np.abs(sim_data["SimTime"] - sim_trigger_time))
    
    sim_sync_data = sim_data.iloc[sim_trigger_index:]
    
    sim_sync_data["sync_time_stamp"] = sim_sync_data["SimTime"] - trigger_time

    return sim_sync_data  # Return the synchronized Simulator data