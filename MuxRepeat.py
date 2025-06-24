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

    if recording:
        mouse.Listener.stop()
        keyboard.Listener.stop()

    play_btn.configure(state="disabled" if not events else "normal")

def play():
    global playing, status
    playing = True
    status = "Playing"
    play_beep(status)
    update_status_label()
    
    if not events:
        return

    start_time = events[0]["time"]
    while playing:
        for i, event in enumerate(events):
            if not playing:
                break
            
            delay = max(event["time"] - start_time, 0)
            if i > 0:
                prev_event = events[i - 1]
                real_duration = event["time"] - prev_event["time"]
                if real_duration > 0:
                    time.sleep(real_duration)

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

        start_time = time.time()

def save_to_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            json.dump(events, file, indent=4)
        global status
        status = "Recording Saved!"
        play_beep(status)
        update_status_label()

def load_from_file():
    global events, status, playing
    file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "r") as file:
                events = json.load(file)
                status = "Recording Loaded!"
                play_beep(status)
                update_status_label()
                play_btn.configure(state="normal" if events else "disabled")
                playing = bool(events)
                status = "Ready to Play" if events else "No Events in File"
                update_status_label()
        except Exception as e:
            status = "Failed to Load"
            play_beep(status)
            update_status_label()
            print("Error loading file:", e)

# Function to update the status label with color coding
def update_status_label():
    status_colors = {
        "Recording": "#FF3B30",  # macOS red
        "Playing": "#34C759",   # macOS green
        "Stopped": "#FF9500",   # macOS orange
        "Ready": "#007AFF",     # macOS blue
        "Recording Saved!": "#34C759",
        "Recording Loaded!": "#34C759",
        "No Events in File": "#FF3B30",
        "Failed to Load": "#FF3B30"
    }
    status_label.configure(text=f"Status: {status}", text_color=status_colors.get(status, "#FFFFFF"))
    app.after(100, update_status_label)

# Keyboard shortcuts
def handle_keypress(event):
    if event.char == 'r':
        record()
    elif event.char == 's':
        stop()
    elif event.char == 'p' and play_btn.cget("state") == "normal":
        threading.Thread(target=play, daemon=True).start()

# GUI Setup
ctk.set_appearance_mode("light")  # Use light mode for macOS-like aesthetic
ctk.set_default_color_theme("blue")  # macOS blue accents

app = ctk.CTk()
app.geometry("600x350")
app.title("Mux Repeat")
app.resizable(False, False)  # Fixed size for a polished look

try:
    app.iconbitmap("MuxRepeater.ico")
except:
    print("MuxRepeater.ico file not found!")

# Main frame with frosted glass effect
main_frame = ctk.CTkFrame(app, fg_color="#F5F5F5", corner_radius=12)
main_frame.pack(pady=20, padx=20, fill="both", expand=True)

# Toolbar frame for status and secondary actions
toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
toolbar_frame.pack(pady=10, fill="x")

status_label = ctk.CTkLabel(toolbar_frame, text=f"Status: {status}", font=("SF Pro Display", 14), text_color="#007AFF")
status_label.pack(side="left", padx=10)

# Save and Load buttons with icons
save_btn = ctk.CTkButton(
    toolbar_frame, text="💾 Save", width=80, height=32, corner_radius=8,
    fg_color="#007AFF", hover_color="#005BB5", command=save_to_file
)
save_btn.pack(side="right", padx=5)

load_btn = ctk.CTkButton(
    toolbar_frame, text="📂 Load", width=80, height=32, corner_radius=8,
    fg_color="#007AFF", hover_color="#005BB5", command=load_from_file
)
load_btn.pack(side="right", padx=5)

# Control frame for main buttons
control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
control_frame.pack(pady=20)

# Main control buttons
record_btn = ctk.CTkButton(
    control_frame, text="● Record", width=80, height=160, corner_radius=20,
    fg_color="#FF3B30", hover_color="#D32F2F", font=("SF Pro Display", 20),
    command=record
)
record_btn.grid(row=0, column=0, padx=10)

stop_btn = ctk.CTkButton(
    control_frame, text="■ Stop", width=100, height=160, corner_radius=20,
    fg_color="#FF9500", hover_color="#F57C00", font=("SF Pro Display", 20),
    command=stop
)
stop_btn.grid(row=0, column=1, padx=10)

play_btn = ctk.CTkButton(
    control_frame, text="▶ Play", width=120, height=160, corner_radius=20,
    fg_color="#34C759", hover_color="#2E7D32", font=("SF Pro Display", 20),
    command=lambda: threading.Thread(target=play, daemon=True).start()
)
play_btn.grid(row=0, column=2, padx=10)
play_btn.configure(state="disabled" if not events else "normal")

# Watermark with hover effect
def on_watermark_hover_in(e):
    watermark.configure(text="Credits: Stoobid @ Exalux, v2025.06.24-01", text_color="#007AFF")

def on_watermark_hover_out(e):
    watermark.configure(text="Made by Stoobid", text_color="#8E8E93")

watermark = ctk.CTkLabel(
    app, text="Made by MuxAI", font=("SF Pro Text", 10), text_color="#8E8E93",
    fg_color="#E8ECEF", corner_radius=8, width=200, height=20
)
watermark.pack(side="bottom", pady=10)
watermark.bind("<Enter>", on_watermark_hover_in)
watermark.bind("<Leave>", on_watermark_hover_out)

# Bind keyboard shortcuts
app.bind('<KeyPress>', handle_keypress)

# Start status update loop
app.after(100, update_status_label)
app.mainloop()
