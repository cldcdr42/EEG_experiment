import serial
import time

ser = serial.Serial("COM3", 9600)
ser.close()
ser.open()
data = []

# Send character 'S' to start the program
while True:
    number = str(input("Type number: "))
    print("Inputted number: " + number)
    ser.write(number.encode()+"\n".encode())
    time.sleep(4)
