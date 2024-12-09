from pylsl import StreamInlet, resolve_stream
from time import sleep, strftime
from pathlib import Path
import concurrent.futures
import serial
import csv
from threading import Lock

def find_stream_source(use_test_source=False):
    """
    Finds sourse of data stream. Returns object __inlet__, which can be used to 
    get timestamps and values.


    Use use_test_source for debugging:
    If True, returns inlet for test source provided from SendData.py
    If False, returns inlet for direct source from NVX36 when:
        1) NVX36 is connected
        2) NeoRec is running and streaming LSL data
    """

    if use_test_source == True:
        return StreamInlet(resolve_stream()[0])
    else:
        return StreamInlet(resolve_stream('name', 'NVX36_Data')[0])

def find_serial_port(COMPORT="COM5"):
    """
    Finds COM port for connected Arduino

    Does not work now, manually set COMx (x - assigned number to connected arduino)

    returns object Serial, which can be used to send or read data from COM-port
    """
    arduino = serial.Serial(COMPORT, 9600)
     
    intro_message_start = arduino.read()
    sleep(1)
    intro_message_end_bytes = arduino.inWaiting()
    intro_message_start += arduino.read(intro_message_end_bytes)
    print(intro_message_start)

    return arduino

EEG_threshold_value = 1e-3
"""
Value used to send control signlan in auto mode. 

# Threshold value from EEG to activate stepper motor
# threshold = 1e-3
"""

def set_threshold(new_EEG_threshold_value):
    """
    Update threshold value for auto mode 
    """

    EEG_threshold_value = new_EEG_threshold_value


cooldown = 0
"""
Number of samples to skip before the next trigger of control signal
"""

def compare_stream_to_threshold(inlet, EEG_threshold_value, cooldown):
    sample, time = inlet.pull_sample()
    sample = sample[0]
    print(str(time) + "   " + str(sample))
    if sample > EEG_threshold_value and cooldown <= 0:
        return True


def send_rotate_signal(serial_port, angle):
    """
    Finds COM port for connected Arduino

    Does not work now, manually set COMx (x - assigned number to connected arduino)
    """
    serial_port.write(str(angle).encode()+"\n".encode())

    tdata = serial_port.read()
    sleep(1)
    data_left = serial_port.inWaiting()
    tdata += serial_port.read(data_left)
    return tdata


def read_tenso(port, baud_rate):
    """Reads float values from the Arduino COM port and prints them."""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:  # Check if data is available to read
                    line = ser.readline().decode('utf-8').strip()  # Read and decode
                    try:
                        value = float(line)  # Try converting to float
                        print(f"Received: {value}")
                    except ValueError:
                        print(f"Invalid data: {line}")
                else:
                    sleep(0.1)  # Avoid busy-waiting
    except serial.SerialException as e:
        print(f"Serial error: {e}")


def write_to_file(filepath, inlet, start_time):
    """
    writes data in csv file in format: time,sample
    """
    sample, time = inlet.pull_sample()
    sample = sample[0]
    time = time - start_time
    data = [time, sample]

    if not Path(filepath).is_file():
        with open(filepath, 'a', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow(["time [sec]", "value [V]"])

    with open(filepath, 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(data)
    return 0


def start_program(use_test_source=True, COMPORT="COM6", save_data_to_file=False, threshold=0.95, angle=30, cooldown=0):
    """
    Main loop of the program in auto-mode: signal to arduino send using data stream from NVX device
    """
    inlet = find_stream_source(use_test_source)
    _, start_time = inlet.pull_sample()

    arduino_port = COMPORT
    arduino = find_serial_port(arduino_port)

    filepath = "C:\\Users\\User\\Desktop\\" + strftime("%Y%m%d-%H%M%S") + ".csv"
    # fpath = "C:\\Users\\User\\Desktop\\" + strftime("%Y%m%d-%H%M%S")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        temp_cooldown = 0
        while True:
            inlet_process = executor.submit(compare_stream_to_threshold, inlet, threshold, temp_cooldown)
            tenso_process = executor.submit(read_tenso, port="COM6", baud_rate=9600)

            threshold_reached = inlet_process.result()
            
            if threshold_reached:
                temp_cooldown = cooldown
                current_angle = send_rotate_signal(arduino, 90)
                #print(current_angle)
                current_angle = send_rotate_signal(arduino, 60)
                #print(current_angle)
            else:
                temp_cooldown -= 1

            if (save_data_to_file):
                write_to_file(filepath, inlet, start_time)
    return 0

port = ""
with open("C:/Users/User/Desktop/folder/university/Project/config.txt", "r") as file:
    port = file.read().strip()

# auto-mode
# threshold = 1e-4
start_program(use_test_source=False, COMPORT=port, save_data_to_file=True, threshold=1e-4, angle=30, cooldown=5*1000)

# manual-rotation
# arduino=find_serial_port(COMPORT=port)
# send_rotate_signal(arduino, 30)


"""
CTRL+K AND CTRL+C - COMMENT
CTRL+K AND CTRL+U - UNCOMMENT
"""

"""
WORKING VERSION BELOW
"""
# from pylsl import StreamInlet, resolve_stream
# from time import sleep, strftime
# from pathlib import Path
# import concurrent.futures
# import serial
# import csv

# def find_stream_source(use_test_source=False):
#     """
#     Finds sourse of data stream. Returns object __inlet__, which can be used to 
#     get timestamps and values.


#     Use use_test_source for debugging:
#     If True, returns inlet for test source provided from SendData.py
#     If False, returns inlet for direct source from NVX36 when:
#         1) NVX36 is connected
#         2) NeoRec is running and streaming LSL data
#     """

#     if use_test_source == True:
#         return StreamInlet(resolve_stream()[0])
#     else:
#         return StreamInlet(resolve_stream('name', 'NVX36_Data')[0])

# def find_serial_port(COMPORT="COM5"):
#     """
#     Finds COM port for connected Arduino

#     Does not work now, manually set COMx (x - assigned number to connected arduino)

#     returns object Serial, which can be used to send or read data from COM-port
#     """
#     arduino = serial.Serial(COMPORT, 9600)
     
#     intro_message_start = arduino.read()
#     sleep(1)
#     intro_message_end_bytes = arduino.inWaiting()
#     intro_message_start += arduino.read(intro_message_end_bytes)
#     print(intro_message_start)

#     return arduino

# EEG_threshold_value = 1e-3
# """
# Value used to send control signlan in auto mode. 

# # Threshold value from EEG to activate stepper motor
# # threshold = 1e-3
# """

# def set_threshold(new_EEG_threshold_value):
#     """
#     Update threshold value for auto mode 
#     """

#     EEG_threshold_value = new_EEG_threshold_value


# cooldown = 0
# """
# Number of samples to skip before the next trigger of control signal
# """

# def compare_stream_to_threshold(inlet, EEG_threshold_value, cooldown):
#     sample, time = inlet.pull_sample()
#     sample = sample[0]
#     print(str(time) + "   " + str(sample))
#     if sample > EEG_threshold_value and cooldown <= 0:
#         return True

# def send_rotate_signal(serial_port, angle):
#     """
#     Finds COM port for connected Arduino

#     Does not work now, manually set COMx (x - assigned number to connected arduino)
#     """
#     serial_port.write(str(angle).encode()+"\n".encode())

#     tdata = serial_port.read()
#     sleep(1)
#     data_left = serial_port.inWaiting()
#     tdata += serial_port.read(data_left)
#     return tdata

# def write_to_file(filepath, inlet, start_time):
#     """
#     writes data in csv file in format: time,sample
#     """
#     sample, time = inlet.pull_sample()
#     sample = sample[0]
#     time = time - start_time
#     data = [time, sample]

#     if not Path(filepath).is_file():
#         with open(filepath, 'a', encoding='UTF8') as f:
#             writer = csv.writer(f)
#             writer.writerow(["time [sec]", "value [V]"])

#     with open(filepath, 'a', encoding='UTF8') as f:
#         writer = csv.writer(f)
#         writer.writerow(data)
#     return 0

# def start_program(use_test_source=True, COMPORT="COM6", save_data_to_file=False, threshold=0.95, angle=30, cooldown=0):
#     """
#     Main loop of the program in auto-mode: signal to arduino send using data stream from NVX device
#     """
#     inlet = find_stream_source(use_test_source)
#     _, start_time = inlet.pull_sample()

#     arduino_port = COMPORT
#     arduino = find_serial_port(arduino_port)

#     filepath = "C:\\Users\\User\\Desktop\\" + strftime("%Y%m%d-%H%M%S") + ".csv"

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         temp_cooldown = 0
#         while True:
#             inlet_process = executor.submit(compare_stream_to_threshold, inlet, threshold, temp_cooldown)
#             threshold_reached = inlet_process.result()
            
#             if threshold_reached:
#                 temp_cooldown = cooldown
#                 current_angle = send_rotate_signal(arduino, 90)
#                 #print(current_angle)
#                 current_angle = send_rotate_signal(arduino, 60)
#                 #print(current_angle)
#             else:
#                 temp_cooldown -= 1

#             if (save_data_to_file):
#                 write_to_file(filepath, inlet, start_time)
#     return 0

# port = ""
# with open("C:/Users/User/Desktop/folder/university/Project/config.txt", "r") as file:
#     port = file.read().strip()

# # auto-mode
# # threshold = 1e-4
# start_program(use_test_source=False, COMPORT=port, save_data_to_file=True, threshold=1e-4, angle=30, cooldown=5*1000)

# # manual-rotation
# # arduino=find_serial_port(COMPORT=port)
# # send_rotate_signal(arduino, 30)