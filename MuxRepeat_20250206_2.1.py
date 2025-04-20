import json
import time
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import winsound
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key

# Initialize controllers
mouse_controller = MouseController()
keyboard_controller = KeyboardController()

events = []
recording = False
playing = False
status = "Ready"

# Function to play a beep sound based on the current status
def play_beep(status):
    if status == "Recording":
        winsound.Beep(1000, 300)  # High pitch for recording
    elif status == "Stopped":
        winsound.Beep(1500, 300)  # Medium pitch for stop
    elif status == "Playing":
        winsound.Beep(2000, 300)  # Low pitch for playing
    elif status == "Ready":
        winsound.Beep(500, 300)  # Default beep for ready

# Mouse and Keyboard Listeners
def on_click(x, y, button, pressed):
    if recording:
        events.append({"type": "mouse", "event": "click", "x": x, "y": y, "button": str(button), "pressed": pressed, "time": time.time()})

def on_move(x, y):
    if recording:
        events.append({"type": "mouse", "event": "move", "x": x, "y": y, "time": time.time()})

def on_press(key):
    if recording:
        events.append({"type": "keyboard", "event": "press", "key": str(key), "time": time.time()})

def on_release(key):
    if recording:
        events.append({"type": "keyboard", "event": "release", "key": str(key), "time": time.time()})

def record():
    global recording, events, status
    events.clear()
    recording = True
    status = "Recording"
    play_beep(status)
    update_status_label()
    threading.Thread(target=lambda: mouse.Listener(on_click=on_click, on_move=on_move).start(), daemon=True).start()
    threading.Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).start(), daemon=True).start()

def stop():
    global recording, playing, status
    recording = False
    playing = False
    status = "Stopped"
    play_beep(status)
    update_status_label()

def play():
    global playing, status
    playing = True
    status = "Playing"
    play_beep(status)
    update_status_label()
    
    if not events:
        return

    start_time = events[0]["time"]  # Time of the first event
    while playing:
        for i, event in enumerate(events):
            if not playing:  # Stop the playback if 'playing' is set to False
                break
            
            delay = max(event["time"] - start_time, 0)  # Ensure the delay is non-negative
            if i > 0:
                prev_event = events[i - 1]
                # Calculate the real-time duration difference for accuracy
                real_duration = event["time"] - prev_event["time"]
                if real_duration > 0:
                    time.sleep(real_duration)  # Make sure the delay corresponds to real event duration

            if event["type"] == "mouse":
                if event["event"] == "move":
                    mouse_controller.position = (event["x"], event["y"])
                elif event["event"] == "click":
                    button = mouse.Button.left if 'left' in event["button"] else mouse.Button.right
                    if event["pressed"]:
                        mouse_controller.press(button)
                    else:
                        mouse_controller.release(button)
            elif event["type"] == "keyboard":
                key = eval(event["key"])
                if event["event"] == "press":
                    keyboard_controller.press(key)
                elif event["event"] == "release":
                    keyboard_controller.release(key)

        # Once the loop finishes, we start it again from the beginning
        start_time = time.time()  # Reset the start time to the current time to prevent long delays


def save_to_file():
    # Open file dialog to choose the file location
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            json.dump(events, file, indent=4)
        # Update the status after saving the recording
        global status
        status = f"Recording Saved to {file_path}"
        play_beep(status)
        update_status_label()


def load_from_file():
    global events, status, playing, recording
    # Open file dialog to choose the file to load
    file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "r") as file:
                events = json.load(file)
                # If the file is loaded successfully, update the status and playback options
                status = f"Recording Loaded from {file_path}"
                play_beep(status)
                update_status_label()

                # Disable 'Play' if there are no events, and update the status
                if not events:
                    status = "No Events in File"
                    play_beep(status)
                    update_status_label()
                    playing = False  # Disable play button functionality if empty
                    play_btn.configure(state="disabled")  # Disable the play button
                else:
                    playing = True  # Enable play if events are available
                    status = "Ready to Play"
                    play_btn.configure(state="normal")  # Enable the play button
                    update_status_label()
        except Exception as e:
            status = "Failed to Load"
            play_beep(status)
            update_status_label()
            print("Error loading file:", e)


# Function to update the status label in real-time
def update_status_label():
    status_label.configure(text=f"Status: {status}")
    app.after(100, update_status_label)  # Update the label every 100ms to keep it real-time

# GUI Setup
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("400x250")
app.title("Mux Repeat")

frame = ctk.CTkFrame(app)
frame.pack(expand=True)

status_label = ctk.CTkLabel(frame, text=f"Status: {status}", text_color="white")
status_label.grid(row=0, column=1, pady=5)

record_btn = ctk.CTkButton(frame, text="●\nRecord", width=100, height=100, command=record)
record_btn.grid(row=1, column=0, padx=10, pady=10)

stop_btn = ctk.CTkButton(frame, text="■\nStop", width=100, height=100, command=stop)
stop_btn.grid(row=1, column=1, padx=10, pady=10)

play_btn = ctk.CTkButton(frame, text="▶\nPlay", width=100, height=100, command=lambda: threading.Thread(target=play, daemon=True).start())
play_btn.grid(row=1, column=2, padx=10, pady=10)

# Disable play button if no events are loaded
if not events:
    play_btn.configure(state="disabled")
else:
    play_btn.configure(state="normal")


save_btn = ctk.CTkButton(frame, text="💾", width=50, height=50, command=save_to_file)
save_btn.grid(row=2, column=0, padx=5, pady=5)

load_btn = ctk.CTkButton(frame, text="📂", width=50, height=50, command=load_from_file)
load_btn.grid(row=2, column=1, padx=5, pady=5)

watermark = ctk.CTkLabel(app, text="Made by MuxAI", font=("Arial", 10), fg_color="grey", corner_radius=5, width=600, height=20)
watermark.pack(side="bottom")

app.mainloop()
