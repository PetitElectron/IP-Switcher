#================== VERSION ==================
VERSION = "1.0.0"

# ================= IMPORTS =================
import os
import socket
import sys
import subprocess
import re

import tkinter as tk
from tkinter import ttk, messagebox
import tkmacosx as tkm
from tkmacosx import Button

import ipaddress
import json


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def run_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)


# ================= NETWORK =================

def get_network_services():
    proc = run_cmd(["networksetup", "-listallnetworkservices"])

    if proc.returncode != 0:
        print("ERROR list services:", proc.stderr)
        return []

    services = []

    for line in proc.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        # Skip header lines that mention "asterisk" (English) or "astérisque" (French)
        low = line.lower()
        if "asterisk" in low or "astérisque" in low:
            continue

        # Services désactivés commencent par *
        if line.startswith("*"):
            continue

        services.append(line)

    return services

def get_device_for_service(service):
    proc = run_cmd(["networksetup", "-listnetworkserviceorder"])

    if proc.returncode != 0:
        return None

    current_service = None

    for line in proc.stdout.splitlines():
        line = line.strip()

        # Lines like "(1) Wi-Fi" -> capture service name after numeric index
        m = re.match(r'^\(\d+\)\s*(.+)$', line)
        if m:
            current_service = m.group(1).strip()
            continue

        # Other lines can contain "Hardware Port: ..., Device: en0" etc.
        if "device:" in line.lower() and current_service == service:
            # try to extract the device token
            mdev = re.search(r'Device:\s*([^\s,)]+)', line, flags=re.IGNORECASE)
            if mdev:
                return mdev.group(1).strip()
            # fallback parsing
            return line.split("Device:", 1)[1].split(")")[0].strip()

    return None


def is_service_active(service):
    device = get_device_for_service(service)

    if not device:
        return False

    proc = run_cmd(["ifconfig", device])

    if proc.returncode != 0:
        return False

    output = proc.stdout.lower()

    return "status: active" in output


def get_interfaces():
    return [
        service
        for service in get_network_services()
        if is_service_active(service)
    ]


def get_current_ip(interface):
    proc = run_cmd(["networksetup", "-getinfo", interface])

    if proc.returncode != 0:
        print("ERROR getinfo:", proc.stderr)
        return None, None

    ip = None
    mask = None

    for line in proc.stdout.splitlines():
        line = line.strip()

        if line.startswith("IP address:"):
            value = line.split(":", 1)[1].strip()
            if value and value != "none":
                ip = value

        elif line.startswith("Subnet mask:"):
            value = line.split(":", 1)[1].strip()
            if value and value != "none":
                mask = value

    return ip, mask


def set_static_ip(interface, ip, mask):
    router = "0.0.0.0"

    proc = run_cmd([
        "networksetup",
        "-setmanual",
        interface,
        ip,
        mask,
        router
    ])

    if proc.returncode != 0:
        print("ERROR set static:", proc.stderr)

    return proc.returncode == 0


def set_dhcp(interface):
    proc = run_cmd([
        "networksetup",
        "-setdhcp",
        interface
    ])

    if proc.returncode != 0:
        print("ERROR set DHCP:", proc.stderr)

    return proc.returncode == 0

# ================= PRESETS =================

USER_HOME = os.environ.get("IP_SWITCHER_USER_HOME", os.path.expanduser("~"))

APPDATA_DIR = os.path.join(USER_HOME, "Library/Application Support", "IPSwitcher")
os.makedirs(APPDATA_DIR, exist_ok=True)

PRESET_FILE = os.path.join(APPDATA_DIR, "presets.json")

DEFAULT_PRESETS = {
    "Dante (DHCP)": {"dhcp": True},
    "LA-Net": {"ip": "192.168.1.0", "mask": "255.255.255.0"},
    "Bolero": {"ip": "192.168.0.0", "mask": "255.255.255.0"},
    "Art-Net (Official 2.x)":{"ip":"2.0.0.0","mask":"255.0.0.0"},
    "Lighting (10.x)": {"ip": "10.0.0.0", "mask": "255.0.0.0"},
}


def load_presets():
    if not os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "w") as f:
            json.dump(DEFAULT_PRESETS, f, indent=4)
        return DEFAULT_PRESETS.copy()

    with open(PRESET_FILE, "r") as f:
        return json.load(f)


def save_presets(data):
    try:
        with open(PRESET_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("Save error", f"Could not save presets:\n\n{e}\n\nPath\n{PRESET_FILE}")
        return False
    
presets = load_presets()


# ================= THEME =================

BG_MAIN = "#111418"
BG_PANEL = "#1a1f26"
BG_INPUT = "#202630"
ACCENT = "#4fd1c5"
TEXT_MAIN = "#e6edf3"
TEXT_MUTED = "#9aa4af"
FONT = ("Arial Narrow MS", 15)

root = tk.Tk()
root.update_idletasks()
root.title(f"IP Switcher v{VERSION}")
root.configure(bg=BG_MAIN)



try:
    icon_img = tk.PhotoImage(file=resource_path("icon.png"))
    root.iconphoto(True, icon_img)
except:
    pass

"""Window config"""

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - 520) // 2
y = (screen_height - 415) // 2
root.geometry(f"520x415+{x}+{y}")

root.minsize(520, 415)
root.resizable(False, False)


style = ttk.Style()
style.theme_use("clam")

style.configure("TCombobox",
                fieldbackground=BG_INPUT,
                background=BG_INPUT,
                foreground=TEXT_MAIN,
                arrowcolor=ACCENT,
                bordercolor=BG_INPUT)

style.map("TCombobox",
          fieldbackground=[("readonly", BG_INPUT)],
          background=[("readonly", BG_INPUT)],
          foreground=[("readonly", TEXT_MAIN)])


main_frame = tk.Frame(root, bg=BG_PANEL)
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)


# ================= UI =================

tk.Label(main_frame, text="Interface",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=0, column=1, sticky="w", padx=15)

iface_var = tk.StringVar()
iface_combo = ttk.Combobox(main_frame,
                           textvariable=iface_var,
                           state="readonly",
                           values=get_interfaces(),
                           width=70)
iface_combo.grid(row=1, column=1, sticky="w", pady=5, padx=15)


tk.Label(main_frame, text="Preset",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=2, column=1, sticky="w", pady=(20, 5), padx=15)

preset_var = tk.StringVar()
preset_combo = ttk.Combobox(main_frame,
                            textvariable=preset_var,
                            state="readonly",
                            values=list(presets.keys()),
                            width=70)
preset_combo.grid(row=3, column=1, sticky="w", pady=5, padx=15)


tk.Label(main_frame, text="IP Address",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=4, column=1, sticky="w", pady=(15, 0), padx=15)

ip_frame = tk.Frame(main_frame, bg=BG_PANEL)
ip_frame.grid(row=5, column=1, sticky="w", padx=15)

ip_vars = []


tk.Label(main_frame, text="Subnet Mask",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=6, column=1, sticky="w", pady=(15, 0), padx=15)

mask_var = tk.StringVar()
mask_frame = tk.Frame(main_frame, bg=BG_PANEL)
mask_frame.grid(row=7, column=1, sticky="w", padx=15)
mask_frame.columnconfigure(0, weight=1)



# ================= IP FIELDS =================

def build_ip_fields(ip, mask):
    global ip_vars
    for w in ip_frame.winfo_children():
        w.destroy()

    ip_vars = []
    ip_octets = ip.split(".")
    mask_octets = mask.split(".")

    for i in range(4):
        var = tk.StringVar(value=ip_octets[i])
        ip_vars.append(var)

        if mask_octets[i] == "255":
            entry = tk.Entry(ip_frame,
                             textvariable=var,
                             width=4,
                             state="readonly",
                             readonlybackground=BG_PANEL,
                             highlightbackground=BG_PANEL,
                             fg=TEXT_MUTED,
                             font=FONT,
                             justify="center",
                             relief="flat")
        else:
            entry = tk.Entry(ip_frame,
                             textvariable=var,
                             width=4,
                             bg=BG_INPUT,
                             fg=ACCENT,
                             highlightbackground=BG_INPUT,
                             font=FONT,
                             justify="center",
                             relief="flat")

        entry.pack(side="left")

        if i < 3:
            tk.Label(ip_frame, text=".",
                     bg=BG_PANEL,
                     fg=TEXT_MAIN,
                     font=FONT).pack(side="left")

# ================= MASK FIELDS =================

def build_mask_fields(mask):
    for w in mask_frame.winfo_children():
        w.destroy()

    if not mask:
        return

    mask_octets = mask.split(".")
    if len(mask_octets) != 4:
        return

    for i in range(4):
        entry = tk.Entry(mask_frame,
                         width=4,
                         readonlybackground=BG_PANEL,
                         highlightbackground=BG_PANEL,
                         fg=TEXT_MUTED,
                         font=FONT,
                         justify="center",
                         relief="flat")

        entry.insert(0, mask_octets[i])
        entry.config(state="readonly")

        entry.pack(side="left", padx=2)

        if i < 3:
            tk.Label(mask_frame,
                     text=".",
                     bg=BG_PANEL,
                     fg=TEXT_MAIN,
                     highlightbackground=BG_PANEL,
                     font=FONT).pack(side="left")


# ================= LOGIC =================

def refresh_current():
    iface = iface_var.get()
    if not iface:
        return

    ip, mask = get_current_ip(iface)
    if ip and mask:
        build_ip_fields(ip, mask)
        build_mask_fields(mask)


def on_preset_change(event=None):
    preset = preset_var.get()
    data = presets.get(preset)
    if not data:
        return

    if data.get("dhcp"):
        mask_var.set("")
        for w in ip_frame.winfo_children():
            w.destroy()
        for w in mask_frame.winfo_children():
            w.destroy()
        return

    build_ip_fields(data["ip"], data["mask"])
    build_mask_fields(data["mask"])


def apply():
    iface = iface_var.get()
    preset = preset_var.get()

    if not iface or not preset:
        messagebox.showwarning("Missing selection", "Select interface and preset.")
        return

    data = presets.get(preset)

    if data.get("dhcp"):
        if set_dhcp(iface):
            refresh_current()
            messagebox.showinfo("Success", "DHCP enabled.")
        else:
            messagebox.showerror("Error", "Failed to enable DHCP.")
        return

    mask = data["mask"]

    try:
        full_ip = ".".join([v.get() for v in ip_vars])
        network = ipaddress.IPv4Network(f"{full_ip}/{mask}", strict=False)
        ip_obj = ipaddress.IPv4Address(full_ip)

        if ip_obj == network.network_address or ip_obj == network.broadcast_address:
            messagebox.showerror("Invalid IP", "Invalid host address.")
            return

    except:
        messagebox.showerror("Invalid IP", "Invalid IP format.")
        return

    if set_static_ip(iface, full_ip, mask):
        refresh_current()
        messagebox.showinfo("Success", f"IP set to {full_ip}")
    else:
        messagebox.showerror("Error", "Failed to change IP.")

def add_preset():
    win = tk.Toplevel(root)
    win.title("Add Preset")
    win.configure(bg=BG_PANEL)
    win.geometry("340x340")
    win.resizable(False, False)

    tk.Label(win, text="Preset Name",
             bg=BG_PANEL, fg=TEXT_MAIN,
             font=FONT).pack(pady=(15, 5))

    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var,
             bg=BG_INPUT, fg=TEXT_MAIN,
             font=FONT, highlightbackground=BG_PANEL).pack()

    tk.Label(win, text="Base IP (e.g. 192.168.10.0)",
             bg=BG_PANEL, fg=TEXT_MAIN,
             font=FONT).pack(pady=(15, 5))
    ip_var = tk.StringVar()
    ip_entry = tk.Entry(win,
                        textvariable=ip_var,
                        bg=BG_INPUT,
                        fg=TEXT_MAIN,
                        font=FONT, highlightbackground=BG_PANEL)
    ip_entry.pack()

    tk.Label(win, text="Subnet Mask",
             bg=BG_PANEL, fg=TEXT_MAIN,
             font=FONT).pack(pady=(15, 5))
    mask_var_local = tk.StringVar()
    mask_entry = tk.Entry(win,
                          textvariable=mask_var_local,
                          bg=BG_INPUT,
                          fg=TEXT_MAIN,
                          font=FONT, highlightbackground=BG_PANEL)
    mask_entry.pack()
    
    dhcp_var = tk.BooleanVar()

    def toggle_dhcp():
        if dhcp_var.get():
            ip_var.set("")
            mask_var_local.set("")
            ip_entry.config(state="readonly", readonlybackground="#2a2f38")
            mask_entry.config(state="readonly", readonlybackground="#2a2f38")
        else:
            ip_entry.config(state="normal", bg=BG_INPUT)
            mask_entry.config(state="normal", bg=BG_INPUT)


    tk.Checkbutton(win,
                   text="DHCP",
                   variable=dhcp_var,
                   command=toggle_dhcp,
                   bg=BG_PANEL,
                   fg=TEXT_MAIN,
                   selectcolor=BG_PANEL,
                   font=FONT).pack(pady=10)

    def confirm():
        name = name_var.get().strip()

        if not name:
            messagebox.showerror("Error", "Preset name required.")
            return

        if dhcp_var.get():
            presets[name] = {"dhcp": True}
        else:
            try:
                ipaddress.IPv4Network(f"{ip_var.get()}/{mask_var_local.get()}", strict=False)
            except:
                messagebox.showerror("Error", "Invalid IP or subnet.")
                return

            presets[name] = {
                "ip": ip_var.get(),
                "mask": mask_var_local.get()
            }

        if save_presets(presets):
            preset_combo["values"] = list(presets.keys())
            messagebox.showinfo("Success", "Preset saved.")
            win.destroy()

    tkm.Button(win,
              text="Confirm",
              command=confirm,
              bg=ACCENT,
              highlightbackground=ACCENT,
              borderless=1,
              fg="#000000",
              font=FONT,
              relief="flat",
              padx=15,
              pady=5).pack(pady=15)


def delete_preset():
    preset = preset_var.get()

    if not preset:
        messagebox.showwarning("Warning", "Select a preset first.")
        return

    if not messagebox.askyesno("Confirm", f"Delete preset '{preset}'?"):
        return

    presets.pop(preset, None)

    if save_presets(presets):
        preset_combo["values"] = list(presets.keys())
        preset_var.set("")
        for w in ip_frame.winfo_children():
            w.destroy()
        for w in mask_frame.winfo_children():
            w.destroy()
        messagebox.showinfo("Deleted", "Preset removed.")


# ================= BUTTONS =================

btn_frame = tk.Frame(main_frame, bg=BG_PANEL)
btn_frame.grid(row=8, column=1, pady=25)

tkm.Button(btn_frame, text="Apply",
          command=apply,
          bg=ACCENT,
          highlightbackground=ACCENT,
          fg="#000000",
          font=FONT,
          relief="flat",
          borderless=1,
          padx=15,
          pady=10).pack(side="left", padx=5)

tkm.Button(btn_frame, text="Add Preset",
          command=add_preset,
          bg=BG_INPUT,
          highlightbackground=BG_INPUT,
          fg=TEXT_MAIN,
          relief="flat",
          borderless=1,
          font=FONT,
          pady=6).pack(side="left", padx=5)

tkm.Button(btn_frame, text="Delete Preset",
          command=delete_preset,
          bg=BG_INPUT,
          highlightbackground=BG_INPUT,
          fg="#ff5c5c",
          relief="flat",
          borderless=1,
          font=FONT,
          pady=6).pack(side="left", padx=5)

# ================ EXEC ==================

iface_combo.bind("<<ComboboxSelected>>", lambda e: refresh_current())
preset_combo.bind("<<ComboboxSelected>>", on_preset_change)

root.mainloop()
