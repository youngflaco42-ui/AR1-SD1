import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time

BAUD_RATE = 115200

ser = None
ready = False

# ---------------------------------------------------------
# SERIAL FUNCTIONS
# ---------------------------------------------------------
def list_com_ports():
    ports = []
    for p in serial.tools.list_ports.comports():
        desc = p.description if p.description else ""
        ports.append(f"{p.device} - {desc}".strip(" -"))
    return ports

def selected_port_device():
    val = port_var.get().strip()
    if not val:
        return ""
    return val.split(" - ")[0].strip()

def connect_serial():
    global ser, ready
    ready = False

    if ser and ser.is_open:
        ser.close()
        ser = None

    dev = selected_port_device()
    if not dev:
        status_var.set("⚠ Select a port first.")
        return

    try:
        ser = serial.Serial(dev, BAUD_RATE, timeout=1)
        time.sleep(2)  # allow Arduino to reset
        status_var.set(f"✔ Connected to {dev}")
    except Exception as e:
        ser = None
        status_var.set(f"⚠ Serial error: {e}")

def refresh_ports():
    ports = list_com_ports()
    port_combo["values"] = ports
    if ports:
        port_var.set(ports[0])
    status_var.set("Ports refreshed.")

# ---------------------------------------------------------
# VACUUM CONTROL (PIN 5)
# ---------------------------------------------------------
def vacuum_on():
    if ser and ser.is_open:
        ser.write(b"VACUUM_ON\n")

def vacuum_off():
    if ser and ser.is_open:
        ser.write(b"VACUUM_OFF\n")

# ---------------------------------------------------------
# SERVO CONTROL
# ---------------------------------------------------------
def send_angles(a1, a2, a3, a4, a5):
    if not ready:
        return
    if ser and ser.is_open:
        msg = f"{int(a1)},{int(a2)},{int(a3)},{int(a4)},{int(a5)}\n"
        ser.write(msg.encode())

def slider_changed(_=None):
    global ready
    ready = True
    send_angles(gripper.get(), rotation.get(), link2.get(), link1.get(), base.get())

def smooth_move(slider, target):
    current = int(slider.get())
    target = int(target)

    if current == target:
        return

    step = 1 if target > current else -1

    for angle in range(current, target, step):
        slider.set(angle)
        send_angles(gripper.get(), rotation.get(), link2.get(), link1.get(), base.get())
        time.sleep(0.01)

    slider.set(target)
    send_angles(gripper.get(), rotation.get(), link2.get(), link1.get(), base.get())

def move_all_slow(targets):
    sliders = [gripper, rotation, link2, link1, base]
    for slider, target in zip(sliders, targets):
        smooth_move(slider, target)

def go_home():
    global ready
    ready = True
    move_all_slow([90, 90, 90, 90, 90])

# ---------------------------------------------------------
# GUI SETUP
# ---------------------------------------------------------
root = tk.Tk()
root.title("Robot Arm Controller")
root.geometry("480x760")

DEFAULT_ANGLE = 90

# ---- SERIAL FRAME
serial_frame = tk.LabelFrame(root, text="Serial Connection", padx=10, pady=10)
serial_frame.pack(fill="x", padx=15, pady=10)

port_var = tk.StringVar()
port_combo = ttk.Combobox(serial_frame, textvariable=port_var, state="readonly", width=45)
port_combo.grid(row=0, column=0, columnspan=2, sticky="we", padx=5, pady=5)

btn_refresh = tk.Button(serial_frame, text="Refresh Ports", command=refresh_ports)
btn_refresh.grid(row=1, column=0, sticky="we", padx=5, pady=5)

btn_connect = tk.Button(serial_frame, text="Connect", command=connect_serial)
btn_connect.grid(row=1, column=1, sticky="we", padx=5, pady=5)

status_var = tk.StringVar(value="Select port and click Connect.")
status_label = tk.Label(serial_frame, textvariable=status_var, anchor="w")
status_label.grid(row=2, column=0, columnspan=2, sticky="we", padx=5, pady=5)

refresh_ports()

# ---- SERVO SLIDERS
sliders_frame = tk.LabelFrame(root, text="Servos", padx=10, pady=10)
sliders_frame.pack(fill="x", padx=15, pady=10)

gripper  = tk.Scale(sliders_frame, from_=60, to=125, orient="horizontal",
                    label="GRIPPER (Pin 10)", command=slider_changed)
rotation = tk.Scale(sliders_frame, from_=0, to=180, orient="horizontal",
                    label="ROTATION (Pin 9)", command=slider_changed)
link2    = tk.Scale(sliders_frame, from_=0, to=180, orient="horizontal",
                    label="LINK 2 (Pin 8)", command=slider_changed)
link1    = tk.Scale(sliders_frame, from_=0, to=180, orient="horizontal",
                    label="LINK 1 (Pin 7)", command=slider_changed)
base     = tk.Scale(sliders_frame, from_=0, to=180, orient="horizontal",
                    label="BASE (Pin 6)", command=slider_changed)

for s in (gripper, rotation, link2, link1, base):
    s.set(DEFAULT_ANGLE)
    s.pack(fill="x", padx=10, pady=5)

# ---- VACUUM CONTROL
vacuum_frame = tk.LabelFrame(root, text="Vacuum Pump Control (Relay Pin 5)", padx=10, pady=10)
vacuum_frame.pack(fill="x", padx=15, pady=10)

btn_vac_on = tk.Button(vacuum_frame, text="VACUUM ON",
                       font=("Arial", 12, "bold"),
                       bg="#90ee90",
                       command=vacuum_on)
btn_vac_on.pack(side="left", expand=True, fill="x", padx=5)

btn_vac_off = tk.Button(vacuum_frame, text="VACUUM OFF",
                        font=("Arial", 12, "bold"),
                        bg="#ff7f7f",
                        command=vacuum_off)
btn_vac_off.pack(side="right", expand=True, fill="x", padx=5)

# ---- HOME BUTTON
btn_home = tk.Button(root, text="HOME POSITION",
                     font=("Arial", 14, "bold"),
                     bg="#d0d0ff",
                     command=go_home)
btn_home.pack(pady=15)

# ---- WARNING
warning_label = tk.Label(root,
    text="⚠ HOME ROBOT BEFORE POWERING OFF",
    font=("Arial", 11, "bold"),
    fg="yellow",
    bg="black")
warning_label.pack(fill="x", padx=15, pady=10)

root.mainloop()
