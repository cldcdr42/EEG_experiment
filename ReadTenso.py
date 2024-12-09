import serial
import concurrent.futures
import time
import csv
from threading import Lock

# Lock to synchronize file writing across threads
file_lock = Lock()

def write_to_csv(file_name, data):
    """Writes a row of data to a CSV file."""
    with file_lock:
        with open(file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

def read_floats_from_com_port(port, baud_rate, file_name):
    """Reads float values from the first Arduino COM port and writes them to a CSV file."""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:  # Check if data is available to read
                    line = ser.readline().decode('utf-8').strip()  # Read and decode
                    try:
                        value = float(line)  # Try converting to float
                        print(f"Float Received: {value}")
                        # Write to CSV
                        write_to_csv(file_name, ["Float", time.strftime("%Y-%m-%d %H:%M:%S"), value])
                    except ValueError:
                        print(f"Invalid float data: {line}")
                else:
                    time.sleep(0.1)  # Avoid busy-waiting
    except serial.SerialException as e:
        print(f"Serial error (float reader): {e}")

def read_integers_from_com_port(port, baud_rate, file_name):
    """Reads integer values from the second Arduino COM port and writes them to a CSV file."""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:  # Check if data is available to read
                    line = ser.readline().decode('utf-8').strip()  # Read and decode
                    try:
                        value = int(line)  # Try converting to integer
                        print(f"Integer Received: {value}")
                        # Write to CSV
                        write_to_csv(file_name, ["Integer", time.strftime("%Y-%m-%d %H:%M:%S"), value])
                    except ValueError:
                        print(f"Invalid integer data: {line}")
                else:
                    time.sleep(0.1)  # Avoid busy-waiting
    except serial.SerialException as e:
        print(f"Serial error (integer reader): {e}")

def main():
    # Specify your COM ports and baud rates
    float_com_port = "COM3"  # COM port for the first Arduino
    int_com_port = "COM4"    # COM port for the second Arduino
    baud_rate = 9600         # Match the baud rate in your Arduino code

    # CSV file name
    csv_file_name = "C:/Users/User/Desktop/" + time.strftime("%Y%m%d-%H%M%S") + "_measurements.csv"

    # Write the header to the CSV file
    with open(csv_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Type", "Timestamp", "Value"])

    # Use ThreadPoolExecutor to run both readers in separate threads
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_float = executor.submit(read_floats_from_com_port, float_com_port, baud_rate, csv_file_name)
        future_int = executor.submit(read_integers_from_com_port, int_com_port, baud_rate, csv_file_name)
        
        try:
            # Wait for both threads to complete (indefinitely in this case)
            concurrent.futures.wait([future_float, future_int])
        except KeyboardInterrupt:
            print("Exiting program.")
            # Cancel both threads
            future_float.cancel()
            future_int.cancel()

if __name__ == "__main__":
    main()
