import csv
import serial
from pylsl import StreamInlet, resolve_stream

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
        return StreamInlet(resolve_stream()[0])
    else:
        return StreamInlet(resolve_stream('name', 'NVX36_Data')[0])

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

def read_eeg_data(inlet, file_path, stop_event, eeg_timestamp_list, lock):
    first_read_flag = True
    while not stop_event.is_set():  # Check if stop event is triggered
        try:
            sample, timestamp = inlet.pull_sample()

            current_timestamp = time.perf_counter()

            if first_read_flag:
                start_timestamp = current_timestamp
                first_read_flag = False
            
            """
            if first_read_flag:
                    start_timestamp = timestamp
                    first_read_flag = False
            """

            with lock:  # Ensure safe access to the list
                    eeg_timestamp_list.append(current_timestamp)

            write_to_csv(file_path, [current_timestamp - start_timestamp, sample[0]])
        except Exception as e:
            print(f"EEG reading error: {e}")
            continue
            #time.sleep(0.1)  # Small sleep to avoid tight loop if error occurs

def read_ard_data(serial_port, file_path, stop_event, ard_timestamp_list, lock):
    first_read_flag = True
    global drift_rate
    while not stop_event.is_set():  # Check if stop event is triggered
        if serial_port.in_waiting > 0:
            try:
                value = serial_port.readline().decode('UTF-8').strip()
                
                current_timestamp = time.perf_counter()

                if first_read_flag:
                    start_timestamp = current_timestamp
                    first_read_flag = False
                
                with lock:  # Ensure safe access to the list
                    ard_timestamp_list.append(current_timestamp)

                write_to_csv(file_path, [current_timestamp - start_timestamp + drift_rate, value])
            except Exception as e:
                print(f"Arduino reading error: {e}")
                continue
                #time.sleep(0.1)  # Small sleep to avoid tight loop if error occurs
        else:
            continue
            #time.sleep(0.01)


def sync_drift(eeg_timestamp_list, ard_timestamp_list, stop_event, lock):
    """
    Calculate and log the time drift between EEG and Arduino timestamps every 60 seconds.
    """
    interval = 1  # Check every second
    elapsed_time = 0
    global drift_rate

    while not stop_event.is_set():
 
        time.sleep(interval)
        elapsed_time += interval
        if elapsed_time >= 60:
            print("HIII")
            with lock:
                latest_eeg_time = eeg_timestamp_list[-1]
                latest_ard_time = ard_timestamp_list[-1]

                drift = latest_ard_time - latest_eeg_time
                if drift > 0:
                    drift_rate = -drift
                else:
                    drift_rate = drift

                print(f"Time drift: {drift_rate:.6f} seconds")
                print("Ardiuno: " + str(latest_ard_time))
                print("EEG " + str(latest_eeg_time))

                eeg_timestamp_list.clear()
                ard_timestamp_list.clear()
                elapsed_time = 0


def main():
    # Create shared stop event for threads
    stop_event = threading.Event()

    # Create CSV files
    eeg_file = initialize_csv('measurements/', 'EEG', ['Timestamp', 'Inlet_value'])
    ard_file = initialize_csv('measurements/', 'Arduino', ['Timestamp', 'Weight'])
    log_file = initialize_csv('measurements/', 'logs', ['log_data'])

    write_to_csv(log_file, ['Name', 'Time', 'Author', 'Attempt'])

    # Read COM_PORT and baudrate from config file
    with open("config", "r") as file:
        com_port = file.readline().strip()
        baud_rate = file.readline().strip()

    # Initialize the Arduino and EEG sources
    arduino = find_ard_port(com_port, baud_rate)
    if not arduino:
        print("Failed to connect to Arduino. Exiting.")
        return

    inlet = find_eeg_source(use_test_source=True)

    eeg_timestamp_list = []
    ard_timestamp_list = []
    lock = threading.Lock()

    global drift_rate
    drift_rate = 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(read_eeg_data, inlet, eeg_file, stop_event, eeg_timestamp_list, lock)
        executor.submit(read_ard_data, arduino, ard_file, stop_event, ard_timestamp_list, lock)
        executor.submit(sync_drift, eeg_timestamp_list, ard_timestamp_list, stop_event, lock)

        try:
            while True:
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("Exiting program...")
            stop_event.set()  # Signal threads to stop

            if arduino.is_open:
                arduino.close()  # Close the serial port

            executor.shutdown(wait=True)  # Wait for threads to clean up

            print("Program successfully terminated.")

if __name__ == "__main__":
    main()
