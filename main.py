import cv2
import time
import random
from threading import Thread
import tkinter as tk
from tkinter import ttk
import numpy as np
from geopy.distance import geodesic
from PIL import Image, ImageTk
from gps3 import gps3
import RPI.GPIO

led_pin = 18

# Initialize GPS active state
session = gps3.GPSDSocket()
data_stream = gps3.DataStream()
session.connect()
session.watch()

# Function to get GPS data 
def get_gps_data():
   for new_data in session:
    if new_data:
        data_stream.unpack(new_data)
        if hasattr(data_stream.TPV, 'lat') and hasattr(data_stream.TPV, 'lon'):
            lat = data_stream.TPV['lat']
            lon = data_stream.TPV['lon']
            speed = data_stream.TPV['speed'] * 2.23694 # Convert MPH
            return lat, lon, speed
        return None, None, None



# Function to get vehicle speed data
def get_vehicle_speed():
    adc_value = read_adc(1)  # Assuming speed sensor is connected to channel 1
    speed = convert_adc_to_speed(adc_value)
    return speed

# Conversion function for vehicle speed
def convert_adc_to_speed(adc_value):
    # Example conversion logic based on specific sensor
    max_adc_value = 1023
    max_speed_mph = 100  # Example maximum speed
    speed = (adc_value / max_adc_value) * max_speed_mph
    return speed
# Function to toggle GPS
def toggle_gps():
    global gps_active, run_start_coords, total_distance, total_runs, run_start_time, canvas, led
    gps_active = not gps_active
    print(f"gps_active toggled to: {gps_active}")
    if gps_active:
        lat, lon, _ = get_gps_data()
        run_start_coords = (lat, lon)
        run_start_time = time.time()
        print(f"GPS started at: {run_start_coords}")
        canvas.itemconfig(led, fill='green')
    else:
        lat, lon, _ = get_gps_data()
        run_end_coords = (lat, lon)
        run_end_time = time.time()
        print(f"GPS stopped at: {run_end_coords}")
        canvas.itemconfig(led, fill='red')
        if run_start_coords and run_end_coords:
            run_distance = geodesic(run_start_coords, run_end_coords).meters * 0.000621371  # Convert meters to miles
            total_distance += run_distance
            total_runs += 1
            run_time = run_end_time - run_start_time
            run_minutes = int(run_time // 60)
            run_seconds = int(run_time % 60)
            run_time_formatted = f"{run_minutes} minutes {run_seconds} seconds"
            run_time_var.set(f"Last Run Time: {run_time_formatted}")
            run_distance_var.set(f"Last Run: {run_distance:.2f} miles")
            total_distance_var.set(f"Total Distance: {total_distance:.2f} miles")
            total_runs_var.set(f"Total Runs: {total_runs}")
            print(f"Run distance: {run_distance:.2f} miles")
            print(f"Total distance: {total_distance:.2f} miles")
            print(f"Total runs: {total_runs}")
            print(f"Run time: {run_time:.2f} seconds")
            print(f"Run time: {run_time_formatted}")
        else:
            print("Run start or end coordinates are missing")
    button_text.set("Stop Spray" if gps_active else "Start Spray")
    print("GPS Active:", gps_active)

# Function to reset run data
def reset_data():
    global run_start_coords, total_distance, total_runs, run_start_time
    run_start_coords = None
    total_distance = 0.0
    total_runs = 0
    run_start_time = 0
    run_time_var.set("Last Run time: 0 Minutes 0 Seconds")
    run_distance_var.set("Last Run: 0.0 miles")
    total_distance_var.set("Total Distance: 0.00 miles")
    total_runs_var.set("total runs: 0")
    print("Run data has been reset")

# Function to update data
def update_data():
    lat, lon, speed = get_gps_data()
    if speed:
        vehicle_speed.set(f"{speed:.2f} mph")
    root.after(1000, update_data)

# GUI Setup
def create_gui():
    global button_text, vehicle_speed, run_distance_var, total_distance_var, total_runs_var, run_time_var, root, video_label, canvas, led
    root = tk.Tk()
    root.title("Smart Crop Spraying System")
    root.configure(bg='#2e2e2e')

    style = ttk.Style()
    style.configure('TButton', font=('Helvetica', 16), padding=10)

    # Vehicle Speed Label
    vehicle_speed_label = ttk.Label(root, text="Vehicle Speed:", font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    vehicle_speed_label.grid(row=0, column=2, padx=10, pady=10, sticky='e')
    vehicle_speed = tk.StringVar()
    vehicle_speed.set("0.00 mph")
    vehicle_speed_value = ttk.Label(root, textvariable=vehicle_speed, font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    vehicle_speed_value.grid(row=0, column=3, padx=10, pady=10, sticky='e')

    # Start Button
    button_text = tk.StringVar()
    button_text.set("Start Spray")
    button = ttk.Button(root, textvariable=button_text, command=toggle_gps, width=10)
    button.grid(row=1, column=1, padx=(10, 5), pady=10, sticky='e')

    # Reset Button
    reset_button = ttk.Button(root, text="Reset Data", command=reset_data, width=10)
    reset_button.grid(row=1, column=2, padx=(5, 10), pady=10, sticky='w')

    # Active LED
    canvas = tk.Canvas(root, width=50, height=50, bg='#2e2e2e', highlightthickness=0)
    canvas.grid(row=1, column=1, pady=10, sticky='w')
    led = canvas.create_oval(10, 10, 40, 40, fill='red')

    # Video Frame
    video_label = ttk.Label(root)
    video_label.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky='n')

    # Run Data Labels
    run_time_var = tk.StringVar()
    run_time_var.set("Last Run time: 0 minutes 0 seconds")
    run_time_label = ttk.Label(root, textvariable=run_time_var, font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    run_time_label.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky='w')

    run_distance_var = tk.StringVar()
    run_distance_var.set("Last Run: 0.00 miles")
    run_distance_label = ttk.Label(root, textvariable=run_distance_var, font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    run_distance_label.grid(row=4, column=0, columnspan=4, padx=10, pady=5, sticky='w')

    total_distance_var = tk.StringVar()
    total_distance_var.set("Total Distance: 0.00 miles")
    total_distance_label = ttk.Label(root, textvariable=total_distance_var, font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    total_distance_label.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky='w')

    total_runs_var = tk.StringVar()
    total_runs_var.set("Total Runs: 0")
    total_runs_label = ttk.Label(root, textvariable=total_runs_var, font=('Helvetica', 16), background='#2e2e2e', foreground='white')
    total_runs_label.grid(row=6, column=0, columnspan=4, padx=10, pady=5, sticky='w')

    root.geometry("800x700")
    update_data()
    root.mainloop()

# Function to update the video feed
def update_video_feed():
    global gps_active  # Ensure gps_active is accessible
    gps_coordinates = []
    cap = cv2.VideoCapture(0)

    def update_frame():
        global gps_active  # Ensure gps_active is accessible here too
        ret, frame = cap.read()
        if ret:
            if gps_active:
                coords = get_gps_data()
                if coords:
                    gps_coordinates.append(coords[:2])

            pixel_coordinates = [(int(lat*10), int(lon*10)) for lat, lon in gps_coordinates if lat and lon]
            frame = draw_lines(frame, pixel_coordinates)

            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)

        root.after(10, update_frame)

    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    update_frame()
    cap.release()


    if not cap.isOpened():
        print("Error: Could not open video device.")
        return
    update_frame()
    cap.release()


# Function to draw lines on the frame
def draw_lines(frame, coordinates):
    for i in range(1, len(coordinates)):
        cv2.line(frame, coordinates[i-1], coordinates[i], (0, 255, 0), 2)
    return frame

# Mock Camera Thread
def camera_thread():
    update_video_feed()

camera_thread = Thread(target=camera_thread)
camera_thread.start()

create_gui()