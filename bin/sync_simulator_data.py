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
import pandas as pd
import tkinter as tk
from tkinter import filedialog

def sync_simulator_data(trigger_time, sim_file = None):

    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.lift()      # Bring the main window to the foreground
    root.attributes('-topmost', True)  # Make sure the window remains on top

    # If sim_file is not provided or empty, prompt user to select one using GUI
    if not sim_file:
        # Call a GUI to select the Simulator folder
        dir_sim = filedialog.askdirectory(title = "Select Simulator folder")

        if not dir_sim:
            root.destroy()
            return None

        sim_files = [file for file in os.listdir(dir_sim) if file.endswith(".dat")]

        # Prompt user to select the xdf file using tkinter
        sim_file = filedialog.askopenfilename(title = "Select the Simulator file to synchronize", initialdir = dir_sim, filetypes = [("Simulator Data", "*.dat")])
        
        if not sim_file:
            root.destroy()
            return None

        root.destroy()  # Close the root window once we're done

    # Grab the event file corresponding to the simulator file
    sim_events_file = os.path.join(os.path.dirname(sim_file), os.path.splitext(os.path.basename(sim_file))[0] + ".evt")

    # Check if file_sim_events exists, if not, display an error
    if not os.path.exists(sim_events_file):
        easygui.msgbox("Event file not found. Please check the file name and try again.", "Error")
        exit()

    # Read simulator data
    sim_data   = pd.read_csv(sim_file, sep = " ")
    event_data = pd.read_csv(sim_events_file, sep = "\s+|#", engine = "python")

    # Get trigger time from event data
    sim_trigger_time  = event_data[event_data["Event_Name"].str.contains("ReferencePoint")]["startTime"].values[0] #First Event
    sim_trigger_index = np.argmin(np.abs(sim_data["SimTime"] - sim_trigger_time))
    
    sim_sync_data = sim_data.iloc[sim_trigger_index:]
    
    sim_sync_data["sync_time_stamp"] = sim_sync_data["SimTime"] - trigger_time

    return sim_sync_data  # Return the synchronized Simulator data