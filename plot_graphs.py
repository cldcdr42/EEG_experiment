import pandas as pd
import matplotlib.pyplot as plt

import os
import glob


"""

measurements\20250120_090935_Arduino.csv

"""

folder_path = "./measurements"
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
csv_files.sort(key=os.path.getmtime, reverse=True)
latest_files = csv_files[:2]

name = "20250120_090935"

file1 = latest_files[0]
file2 = latest_files[1]

# Read your CSVs
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1['force_value [w]'] = pd.to_numeric(df1['force_value [w]'], errors='coerce')
df1 = df1.dropna().reset_index(drop=True)

df2['eeg_value [V]'] = pd.to_numeric(df2['eeg_value [V]'], errors='coerce')
df2 = df2.dropna().reset_index(drop=True)

#df1['Timestamp [sec]'] = df1['Timestamp [sec]'] / 1000

plot_on_separate = True

if plot_on_separate:
    # Plotting on separate plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))  # Two rows, one column

    # Plot data from df1 on the first plot
    ax1.plot(df1['Timestamp [sec]'], df1['force_value [w]'], color='b', label='Weight', linestyle='-')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Weight', color='b')
    ax1.set_title('Weight over Time')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_xlim([0, df1['Timestamp [sec]'].max()])

    # Plot data from df2 on the second plot
    ax2.plot(df2['Timestamp [sec]'], df2['eeg_value [V]'], color='g', label='Inlet Value', linestyle='--')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Inlet Value', color='g')
    ax2.set_title('Inlet Value over Time')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.set_xlim([0, df2['Timestamp [sec]'].max()])

    plt.tight_layout()  # Adjusts the spacing between the plots
    plt.show()
else:
    # Plotting both on the same graph with different y-axes
    fig, ax1 = plt.subplots()

    # Plot data from df1 on the left y-axis
    ax1.plot(df1['Timestamp [sec]'], df1['force_value [w]'], color='b', label='Weight', linestyle='-')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Weight', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_xlim([0, df1['Timestamp [sec]'].max()])

    # Create a second y-axis on the right for df2
    ax2 = ax1.twinx()
    ax2.plot(df2['Timestamp [sec]'], df2['eeg_value [V]'], color='g', label='Inlet Value', linestyle='--')
    ax2.set_ylabel('Inlet Value', color='g')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.set_xlim([0, df2['Timestamp [sec]'].max()])

    plt.title('Weight and Inlet Value over Time')
    plt.show()