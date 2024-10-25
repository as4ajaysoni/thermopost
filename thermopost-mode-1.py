import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def process_file(input_path, output_csv_path, interpolated_csv_path):
    # Define the headers manually
    headers = [
        "Time(s)",
        "Pressure at x=L/4 Tunnel-1(kPa)",
        "Pressure at x=L/2 Tunnel-1(kPa)",
        "Pressure at x=3L/4 Tunnel-1(kPa)",
        "Velocity at x=L/4 Tunnel-1(m/s)",
        "Velocity at x=L/2 Tunnel-1(m/s)",
        "Velocity at x=3L/4 Tunnel-1(m/s)",
        "Pressure Front coach(outside)[kPa]",
        "Pressure Front coach(inside)[kPa]",
        "Pressure Rear coach(outside)[kPa]",
        "Pressure Rear coach(inside)[kPa]",
        "Speed Train(m/s)"
    ]
    
    with open(input_path, 'r') as file:
        lines = file.readlines()
    
    # Extract data lines starting from the 10th row (index 9)
    data_lines = lines[9:]
    
    # Prepare data for DataFrame
    data = []
    for line in data_lines:
        if "Max.value" in line:
            break
        
        row = line.strip().split()
        data.append(row)
    
    df = pd.DataFrame(data, columns=headers)
    
    # Convert columns to appropriate data types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=headers)
    
    # Add the new Distance(m) column
    df["Distance(m)"] = df["Time(s)"] * df["Speed Train(m/s)"]

    # Save DataFrame to CSV
    df.to_csv(output_csv_path, index=False)
    print(f"Data saved to {output_csv_path}")
    
    # Interpolate pressure data to a uniform time grid
    time_start = 0.0    # df['Time(s)'].min()
    time_end = df['Time(s)'].max()
    time_step = 0.1  # Define the time step for interpolation (can be adjusted as needed)
    uniform_time = np.arange(time_start, time_end + time_step, time_step)
    
    pfout_interpolator = np.interp(uniform_time, df['Time(s)'], df['Pressure Front coach(outside)[kPa]'])
    pfin_interpolator = np.interp(uniform_time, df['Time(s)'], df['Pressure Front coach(inside)[kPa]'])
    prout_interpolator = np.interp(uniform_time, df['Time(s)'], df['Pressure Rear coach(outside)[kPa]'])
    prin_interpolator = np.interp(uniform_time, df['Time(s)'], df['Pressure Rear coach(inside)[kPa]'])
    


    # Calculate distance using uniform time and speed average speed
    average_speed = df['Speed Train(m/s)'].mean()
    distance_interpolator = uniform_time * average_speed

    # Create a DataFrame for interpolated data
    interpolated_data = pd.DataFrame({
        'Time(s)': uniform_time,
        'Distance(m)': distance_interpolator,
        'Pressure Front coach(outside)[kPa]': pfout_interpolator,
        'Pressure Front coach(inside)[kPa]': pfin_interpolator,
        'Pressure Rear coach(outside)[kPa]': prout_interpolator,
        'Pressure Rear coach(inside)[kPa]': prin_interpolator

    })
    
    window_size = 40
    # Calculate rolling minimum with a window size of 40
    interpolated_data['rolling-min-PFout'] = interpolated_data['Pressure Front coach(outside)[kPa]'].rolling(window=window_size, min_periods=1).min()
    
    # Replace the first 40 cells with the value from the 41st cell
    if len(interpolated_data) > window_size:
        value_41st_cell = interpolated_data['rolling-min-PFout'].iloc[window_size-1]  # 41st cell has index 40
        interpolated_data.loc[:window_size-1, 'rolling-min-PFout'] = value_41st_cell
    
    # Calculate rolling max
    interpolated_data['rolling-max-PFout'] = interpolated_data['Pressure Front coach(outside)[kPa]'].rolling(window=window_size, min_periods=1).max()

    # Replace the first 40 cells with the value from the 41st cell
    if len(interpolated_data) > window_size:
        value_41st_cell = interpolated_data['rolling-max-PFout'].iloc[window_size-1]  # 41st cell has index 40
        interpolated_data.loc[:window_size-1, 'rolling-max-PFout'] = value_41st_cell

    # Create Delta_PFout column containing Abs(rolling-max-PFout - rolling-min-PFout)
    interpolated_data['Delta_PFout'] = (interpolated_data['rolling-max-PFout'] - interpolated_data['rolling-min-PFout']).abs()


    # Calculate rolling minimum with a window size of 40
    interpolated_data['rolling-min-PRout'] = interpolated_data['Pressure Rear coach(outside)[kPa]'].rolling(window=window_size, min_periods=1).min()
    
    # Replace the first 40 cells with the value from the 41st cell
    if len(interpolated_data) > window_size:
        value_41st_cell = interpolated_data['rolling-min-PRout'].iloc[window_size-1]  # 41st cell has index 40
        interpolated_data.loc[:window_size-1, 'rolling-min-PRout'] = value_41st_cell
    
    # Calculate rolling max
    interpolated_data['rolling-max-PRout'] = interpolated_data['Pressure Rear coach(outside)[kPa]'].rolling(window=window_size, min_periods=1).max()

    # Replace the first 40 cells with the value from the 41st cell
    if len(interpolated_data) > window_size:
        value_41st_cell = interpolated_data['rolling-max-PRout'].iloc[window_size-1]  # 41st cell has index 40
        interpolated_data.loc[:window_size-1, 'rolling-max-PRout'] = value_41st_cell

    # Create Delta_PRout column containing Abs(rolling-max-PRout - rolling-min-PRout)
    interpolated_data['Delta_PRout'] = (interpolated_data['rolling-max-PRout'] - interpolated_data['rolling-min-PRout']).abs()

    # Save interpolated data to CSV
    interpolated_data.to_csv(interpolated_csv_path, index=False)
    print(f"Interpolated data saved to {interpolated_csv_path}")
    
    # Plot data with two subplots
    plt.figure(figsize=(14, 10))

    # Subplot 2: Pressure Front and Rear coach[kPa] vs Time(s)
    plt.subplot(2, 2, 1)
    plt.plot(interpolated_data['Time(s)'], interpolated_data['Pressure Front coach(outside)[kPa]'], linestyle='-', color='k', label='Pressure Front coach(outside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Time(s)'], interpolated_data['Pressure Front coach(inside)[kPa]'], linestyle=':', color='r', label='Pressure Front coach(inside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Time(s)'], interpolated_data['Pressure Rear coach(outside)[kPa]'], linestyle='-', color='k', label='Pressure Rear coach(outside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Time(s)'], interpolated_data['Pressure Rear coach(inside)[kPa]'], linestyle=':', color='r', label='Pressure Rear coach(inside)[kPa]') # if req, marker='o'
    plt.xlabel('Time(s)')
    plt.ylabel('Pressure [kPa]')
    plt.title('Pressure [kPa] vs Distance(m)')
    plt.legend()  # Add legend to the first subplot
    plt.grid(True)

    # Subplot 1: Pressure Front and Rear coach[kPa] vs Distance (m)
    plt.subplot(2, 2, 2)
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Pressure Front coach(outside)[kPa]'], linestyle='-', color='k', label='Pressure Front coach(outside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Pressure Front coach(inside)[kPa]'], linestyle=':', color='r', label='Pressure Front coach(inside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Pressure Rear coach(outside)[kPa]'], linestyle='-', color='k', label='Pressure Rear coach(outside)[kPa]') # if req, marker='o'
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Pressure Rear coach(inside)[kPa]'], linestyle=':', color='r', label='Pressure Rear coach(inside)[kPa]') # if req, marker='o'
    plt.xlabel('Distance (m)')
    plt.ylabel('Pressure [kPa]')
    plt.title('Pressure [kPa] vs Distance(m)')
    plt.legend()  # Add legend to the first subplot
    plt.grid(True)


    # Subplot 3: Delta_PFout and Delta_PRout vs Distance(m)
    plt.subplot(2, 2, 3)
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Delta_PFout'], linestyle='-', color='k', label='ΔPout [kPa] Front') # if req , marker='x'
    plt.plot(interpolated_data['Distance(m)'], interpolated_data['Delta_PRout'], linestyle='-', color='r', label='ΔPout [kPa] Rear') # if req , marker='x'
    plt.xlabel('Distance (m)')
    plt.ylabel('ΔPout [kPa] in Δt = 4 sec')
    plt.title('ΔPout [kPa] in Δt = 4 sec vs Distance(m)')
    # if required plt.axhline(y=3, color='b', linestyle='--', label='Reference Line (0.3)')
    plt.legend()  # Add legend to the second subplot
    plt.grid(True)

    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Process a data file and generate plots.")
    parser.add_argument('-f', '--file', required=True, help="Input filename")
    
    args = parser.parse_args()
    input_path = args.file
    
    # Generate output CSV paths
    base, _ = os.path.splitext(input_path)
    output_csv_path = f"{base}_raw.csv"
    interpolated_csv_path = f"{base}_interpolated.csv"
    
    process_file(input_path, output_csv_path, interpolated_csv_path)

if __name__ == "__main__":
    main()
