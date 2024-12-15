import serial
import csv
from pylsl import StreamInlet, resolve_stream
from time import sleep, time, strftime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from pathlib import Path

# Global locks for synchronized file writing
file_lock = Lock()

# Separate timestamp counters for Arduino and Inlet
arduino_timestamp = 0
inlet_timestamp = 0
last_inlet_time = 0  # Time of the last inlet sample for timestamp calculation


def initialize_csv(file_path, headers):
    """
    Initialize the CSV file with the specified headers if it doesn't already exist.
    """
    with file_lock:
        if not Path(file_path).exists():
            with open(file_path, 'w', newline='', encoding='UTF-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)


def write_to_csv(file_path, data):
    """
    Write a row of data to the CSV file in a thread-safe manner.
    """
    with file_lock:
        with open(file_path, 'a', newline='', encoding='UTF-8') as file:
            writer = csv.writer(file)
            writer.writerow(data)


def find_stream_source(use_test_source=False):
    """
    Locate the LSL data stream and return a StreamInlet for data access.
    """
    if use_test_source:
        return StreamInlet(resolve_stream()[0])
    else:
        return StreamInlet(resolve_stream('name', 'NVX36_Data')[0])


def find_serial_port(com_port, baud_rate=9600):
    """
    Open the specified COM port for Arduino communication.
    """
    try:
        return serial.Serial(com_port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening COM port {com_port}: {e}")
        return None


def read_inlet_data(inlet, file_path):
    """
    Continuously read data from the LSL inlet and write it to a CSV file.
    """
    global inlet_timestamp, last_inlet_time  # Use global variables for inlet timestamp
    while True:
        try:
            sample, timestamp = inlet.pull_sample()
            if sample:
                # If this is the first sample, initialize the start time
                if last_inlet_time == 0:
                    last_inlet_time = timestamp
                
                # Calculate the elapsed time since the last sample
                elapsed_time = timestamp - last_inlet_time
                
                # Update the timestamp (in seconds) and increment it
                inlet_timestamp += elapsed_time
                
                print(f"Inlet Data: {sample[0]} at {inlet_timestamp:.4f}")
                write_to_csv(file_path, [inlet_timestamp, sample[0]])
                
                last_inlet_time = timestamp  # Update the last inlet sample time
        except Exception as e:
            print(f"Error reading inlet data: {e}")
            break


def read_arduino_data(serial_port, file_path):
    """
    Continuously read data from the Arduino serial port and write it to a CSV file.
    The data comes in the format: timestamp,value.
    The first timestamp is written as 0, and all subsequent timestamps are incremented.
    """
    first_timestamp = None  # Variable to store the first timestamp
    last_timestamp = None  # Variable to store the last valid timestamp
    try:
        while True:
            if serial_port.in_waiting > 0:
                line = serial_port.readline().decode('utf-8').strip()
                try:
                    # Split the received line into timestamp and value
                    timestamp, value = line.split(',')
                    timestamp = float(timestamp)  # Convert timestamp to float
                    value = float(value)  # Convert value to float

                    if first_timestamp is None:
                        first_timestamp = timestamp  # Save the first timestamp
                        last_timestamp = timestamp  # Initialize last_timestamp
                        incremented_timestamp = 0.0  # The first timestamp is set to 0
                    else:
                        # Ensure the timestamp is incrementing
                        if timestamp >= last_timestamp:
                            incremented_timestamp = timestamp - first_timestamp
                        else:
                            print(f"Warning: Received timestamp {timestamp} is less than previous timestamp {last_timestamp}. Skipping this reading.")
                            continue  # Skip invalid (decreasing) timestamps
                        
                        last_timestamp = timestamp  # Update last valid timestamp
                    
                    print(f"Arduino Data: {value} at {incremented_timestamp}")
                    write_to_csv(file_path, [incremented_timestamp, value])  # Write incremented timestamp and value to CSV
                except ValueError:
                    print(f"Invalid Arduino data: {line}")
            else:
                sleep(0.1)  # Reduce CPU usage
    except serial.SerialException as e:
        print(f"Error reading Arduino data: {e}")



def main():
    # Configuration
    use_test_source = True  # Set to True for test source
    com_port = "COM6"  # Update as needed
    baud_rate = 9600
    fpath = "C:\\Users\\User\\Desktop\\" + strftime("%Y%m%d-%H%M%S")
    inlet_csv_file_path = fpath + "_inlet_data.csv"
    arduino_csv_file_path = fpath + "_arduino_data.csv"
    
    # CSV Headers
    inlet_headers = ["Timestamp", "Inlet_Value"]
    arduino_headers = ["Timestamp", "Arduino_Value"]

    # Initialize CSV files
    initialize_csv(inlet_csv_file_path, inlet_headers)
    initialize_csv(arduino_csv_file_path, arduino_headers)

    # Find and initialize LSL inlet
    inlet = find_stream_source(use_test_source)

    # Find and initialize Arduino serial port
    arduino = find_serial_port(com_port, baud_rate)
    if not arduino:
        print("Failed to connect to Arduino. Exiting.")
        return

    # Run both reading tasks in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(read_inlet_data, inlet, inlet_csv_file_path)
        executor.submit(read_arduino_data, arduino, arduino_csv_file_path)

        try:
            while True:
                sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Exiting program...")
            executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
