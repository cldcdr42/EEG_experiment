import csv

# Initialize the sum of values and count of rows
total_value = 0
count = 0

# -3.209907410724749e-09
#  3.9229338793637986e-09
#  4.684431285180463e-08

with open("C:/Users/User/Desktop/medium_action.csv", mode='r') as file:
    reader = csv.reader(file)
    
    # Skip the header
    next(reader)
    
    # Iterate through each row in the file
    for row in reader:
        # Skip empty rows or rows with insufficient columns
        if len(row) < 2:
            continue
        
        try:
            # Parse the value in the second column
            value = float(row[1])
            
            # Accumulate the total sum and count the number of rows
            total_value += value
            count += 1
        except ValueError:
            # In case the second column is not a valid float, skip this row
            continue

# Calculate the average
average_value = total_value / count if count != 0 else 0

# Output the average value
print(f"The average value of the second column is: {average_value}")
