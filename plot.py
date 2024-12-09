import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV files into pandas DataFrames
fpath = "C:\\Users\\User\\Desktop\\"
df_inlet = pd.read_csv(fpath + "20241119-121919_inlet_data" + ".csv")  # Replace with your first CSV file path
df_arduino = pd.read_csv(fpath + "20241119-121919_arduino_data" + ".csv")  # Replace with your second CSV file path

# Create a figure with 2 subplots (1 row, 2 columns)
fig, axs = plt.subplots(2, 1, figsize=(10, 10))

# Plotting Inlet_Value vs Timestamp in the first subplot
axs[0].plot(df_inlet['Timestamp'], df_inlet['Inlet_Value'], label='Inlet Value', color='blue')
axs[0].set_title('Inlet Value vs Time')
axs[0].set_xlabel('Timestamp')
axs[0].set_ylabel('Inlet Value')
axs[0].grid(True)
axs[0].legend()

# Plotting Arduino_Value vs Timestamp in the second subplot
axs[1].plot(df_arduino['Timestamp'], df_arduino['Arduino_Value'], label='Arduino Value', color='red', linestyle='--')
axs[1].set_title('Arduino Value vs Time')
axs[1].set_xlabel('Timestamp')
axs[1].set_ylabel('Arduino Value')
axs[1].grid(True)
axs[1].legend()

# Adjust the layout to make it look better
plt.tight_layout()

# Display the plots
plt.show()
