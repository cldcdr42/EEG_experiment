import serial
import time

# Configure the serial port
PORT = "COM3"  # Replace with the virtual/physical serial port name
BAUD_RATE = 9600  # Baud rate
MESSAGE = "Hello, this is serial data!\n"  # Message to send
TIME_INTERVAL = 2  # Interval in seconds between messages

try:
    # Open the serial port
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"Serial port {PORT} opened. Sending data every {TIME_INTERVAL} seconds.")
    print("Open the paired port in another application to view the data.")

    while True:
        # Send the message
        ser.write(MESSAGE.encode('utf-8'))
        print(f"Sent: {MESSAGE.strip()}")
        time.sleep(TIME_INTERVAL)

except serial.SerialException as e:
    print(f"Serial port error: {e}")
except KeyboardInterrupt:
    print("\nProgram stopped by user.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print(f"Serial port {PORT} closed.")
