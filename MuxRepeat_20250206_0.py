import json
import time
import threading
import customtkinter as ctk
import winsound
import tkinter as tk
from tkinter import filedialog
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode

# Initialize controllers
mouse_controller = MouseController()
keyboard_controller = KeyboardController()

events = []
recording = False
playing = False
status = "Idle"

# Lock to ensure only one instance of play/recording at a time
automation_lock = threading.Lock()

def update_status(new_status, color="white"):
    global status
    status = new_status
    status_label.configure(text=f"Status: {status}", text_color=color)

def play_tone(frequency, duration=300):
    threading.Thread(target=winsound.Beep, args=(frequency, duration), daemon=True).start()

def on_click(x, y, button, pressed):
    if recording:
        events.append({"type": "mouse", "event": "click", "x": x, "y": y, "button": str(button), "pressed": pressed, "time": time.time()})

def on_move(x, y):
    if recording:
        events.append({"type": "mouse", "event": "move", "x": x, "y": y, "time": time.time()})

def on_press(key):
    global playing

    # Ignore F1, F2, F3 keys for recording, but handle them for stopping the automation during playback
    if key in [Key.f1, Key.f2, Key.f3]:
        if playing:
            stop()  # Stop automation immediately if these keys are pressed during playback
        return False  # Don't record F1, F2, F3 keys

    if recording:
        events.append({"type": "keyboard", "event": "press", "key": str(key), "time": time.time()})

def on_release(key):
    # Don't record or respond to F1, F2, or F3 keys
    if key in [Key.f1, Key.f2, Key.f3]:
        return False  # Ignore the release of these keys
    if recording:
        events.append({"type": "keyboard", "event": "release", "key": str(key), "time": time.time()})

def record():
    global recording, events
    with automation_lock:
        if recording or playing:  # Prevent recording if already recording or playing
            return
        events.clear()
        recording = True
        update_status("Recording", "red")
        play_tone(1000)
        # Start listeners for mouse and keyboard
        threading.Thread(target=lambda: mouse.Listener(on_click=on_click, on_move=on_move).start(), daemon=True).start()
        threading.Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).start(), daemon=True).start()

def stop():
    global recording, playing
    with automation_lock:
        if not recording and not playing:  # If neither is active, do nothing
            return
        recording = False
        playing = False
        update_status("Idle", "white")
        play_tone(600)

def play():
    global playing
    with automation_lock:
        if recording or playing:  # Prevent playback if already recording or playing
            return
        if not events:
            update_status("Error: No events recorded", "yellow")
            return
        playing = True
        update_status("Playing", "green")
        play_tone(800)
        start_time = events[0]["time"]
        
        while playing:  # Continuous loop for playback
            for event in events:
                if not playing:
                    break
                delay = max(event["time"] - start_time, 0)
                process_event(event, delay)
            start_time = time.time()  # Restart the playback from the beginning

        update_status("Idle", "white")

def process_event(event, delay):
    time.sleep(delay)
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

def save_to_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, "w") as file:
            json.dump(events, file, indent=4)

def load_from_file():
    global events
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, "r") as file:
            events = json.load(file)

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

save_btn = ctk.CTkButton(frame, text="💾", width=50, height=50, command=save_to_file)
save_btn.grid(row=2, column=0, padx=5, pady=5)

load_btn = ctk.CTkButton(frame, text="📂", width=50, height=50, command=load_from_file)
load_btn.grid(row=2, column=1, padx=5, pady=5)

watermark = ctk.CTkLabel(app, text="Made by MuxAI", font=("Arial", 10), fg_color="grey", corner_radius=5, width=600, height=20)
watermark.pack(side="bottom")

keyboard.Listener(on_press=on_press, on_release=on_release).start()

app.mainloop()
