import json
import time
import threading
import customtkinter as ctk
from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key

# Initialize controllers
mouse_controller = MouseController()
keyboard_controller = KeyboardController()

events = []
recording = False
playing = False

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
    global recording, events
    events.clear()
    recording = True
    threading.Thread(target=lambda: mouse.Listener(on_click=on_click, on_move=on_move).start(), daemon=True).start()
    threading.Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).start(), daemon=True).start()

def stop():
    global recording, playing
    recording = False
    playing = False

def play():
    global playing
    playing = True
    start_time = events[0]["time"] if events else time.time()  # Set to first event time
    for event in events:
        if not playing:
            break

        delay = max(event["time"] - start_time, 0)  # Ensure delay is non-negative
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
    with open("automation.json", "w") as file:
        json.dump(events, file, indent=4)

def load_from_file():
    global events
    with open("automation.json", "r") as file:
        events = json.load(file)

# GUI Setup
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("400x400")
app.title("Automation Recorder")

record_btn = ctk.CTkButton(app, text="Record", command=record)
record_btn.pack(pady=10)

stop_btn = ctk.CTkButton(app, text="Stop", command=stop)
stop_btn.pack(pady=10)

play_btn = ctk.CTkButton(app, text="Play", command=lambda: threading.Thread(target=play, daemon=True).start())
play_btn.pack(pady=10)

save_btn = ctk.CTkButton(app, text="Save", command=save_to_file)
save_btn.pack(pady=10)

load_btn = ctk.CTkButton(app, text="Load", command=load_from_file)
load_btn.pack(pady=10)

app.mainloop()
