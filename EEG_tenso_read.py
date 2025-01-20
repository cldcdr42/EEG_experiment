import csv
import serial
from pylsl import StreamInlet, resolve_streams

import pandas as pd

import time
import threading
from concurrent.futures import ThreadPoolExecutor

def initialize_csv(file_path, data_type, headers):
    """
    Initialize the CSV file with the specified headers if it doesn't already exist.
    """
    data_file = file_path + time.strftime("%Y%m%d-%H%M%S") + '_' + data_type + '.csv'
    with open(data_file, 'w', newline='', encoding='UTF-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    return data_file
    
def write_to_csv(file_path, data):
    """
    Write a row of data to the CSV file in a thread-safe manner.
    """
    with open(file_path, 'a', newline='', encoding='UTF-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def find_eeg_source(use_test_source=False):
    """
    Locate the LSL data stream and return a StreamInlet for data access.
    """
    if use_test_source:
        return StreamInlet(resolve_streams()[0])
    else:
        return StreamInlet(resolve_streams('name', 'NVX36_Data')[0])

def find_ard_port(com_port, baud_rate=9600):
    """
    Open the specified COM port for Arduino communication.
    """
    try:
        arduino = serial.Serial(
            com_port,
            baud_rate,
            timeout=1
        )
        
        intro_message_start = arduino.read()
        print(intro_message_start)
        
        return arduino
    except serial.SerialException as e:
        print(f"Error opening COM port {com_port}: {e}")
        return None

def read_eeg_data(inlet, eeg_data, stop_event):
    """
    Start reading data from eeg until keyboard interrupt
    """
    columns = ["Timestamp [sec]", "eeg_value [V]"]

    while not stop_event.is_set():
        sample, timestamp = inlet.pull_sample()
        eeg_data.loc[len(eeg_data)] = [timestamp, sample[0]]
        continue
    
        chunk, timestamp = inlet.pull_chunk(max_samples=256)

        if timestamp:
            new_data = pd.DataFrame(chunk, columns=['eeg_value [V]'])
            new_data["Timestamp [sec]"] = timestamp

            eeg_data = eeg_data.append(new_data)
            #eeg_data.loc[-1] = [timestamp, chunk]
            #print(timestamp, chunk)
        #print("EEG_chunk:", chunk)
        #print("EEG_time:", timestamp)
        #new_eeg_data = pd.DataFrame(chunk, columns=columns[1:])
        #new_eeg_data["Timestamp [sec]"] = timestamp
        #print("EEG: " + str(timestamp) + "   " + str(chunk))
        #eeg_data = pd.concat([eeg_data, new_eeg_data], ignore_index=True)

def read_ard_data(serial_port, ard_data, stop_event):
    """
    Start reading data from arduino until keyboard interrupt
    """
    while not stop_event.is_set():
        if serial_port.in_waiting > 0:
            timestamp, sample = serial_port.readline().decode('UTF-8').strip().split(';')
            #print("Ard: " + str(timestamp) + "   " + str(sample))
            ard_data.loc[len(ard_data)] = [timestamp, sample]

def main():
    # Create shared stop event for threads
    stop_event = threading.Event()

    # Read COM_PORT and baudrate from config file
    with open("config", "r") as file:
        com_port = file.readline().strip()
        baud_rate = file.readline().strip()

    # Initialize the Arduino and EEG sources
    arduino = find_ard_port(com_port, baud_rate)
    if not arduino:
        print("Failed to connect to Arduino. Exiting.")
        return

    # find inlet for eeg
    inlet = find_eeg_source(use_test_source=True)

    # create dataframes to store data
    eeg_data = pd.DataFrame(columns=["Timestamp [sec]", "eeg_value [V]"])
    ard_data = pd.DataFrame(columns=["Timestamp [sec]", "force_value [w]"])

    # start main loop of data collection
    with ThreadPoolExecutor(max_workers=3) as executor:
        print("Startin data collection...")
        executor.submit(read_eeg_data, inlet, eeg_data, stop_event)
        executor.submit(read_ard_data, arduino, ard_data, stop_event)

        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Exiting program gracefully...")

            stop_event.set()  # Signal threads to stop

            if arduino.is_open:
                arduino.close()  # Close the serial port
            
            executor.shutdown(wait=True)  # Wait for threads to clean up
            
            print("Saving data into file before exitting...")

            eeg_filename = "measurements/" + time.strftime("%Y%m%d_%H%M%S") + "_EEG.csv"
            ard_filename = "measurements/" + time.strftime("%Y%m%d_%H%M%S") + "_Arduino.csv"

            eeg_data["Timestamp [sec]"] = pd.to_numeric(eeg_data["Timestamp [sec]"], errors="coerce")
            ard_data["Timestamp [sec]"] = pd.to_numeric(ard_data["Timestamp [sec]"], errors="coerce")

            ard_data = ard_data.drop(index=0).reset_index(drop=True) 
            ard_data["Timestamp [sec]"] = ard_data["Timestamp [sec]"] / 1000

            eeg_data["Timestamp [sec]"] = eeg_data["Timestamp [sec]"] - eeg_data["Timestamp [sec]"].iloc[0]
            ard_data["Timestamp [sec]"] = ard_data["Timestamp [sec]"] - ard_data["Timestamp [sec]"].iloc[0]

            eeg_data.to_csv(eeg_filename, index=False)  # 'index=False' avoids writing row numbers
            ard_data.to_csv(ard_filename, index=False)

            print("Data saved, program successfully terminated.")

if __name__ == "__main__":
    main()
