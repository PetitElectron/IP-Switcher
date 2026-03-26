#================== VERSION ==================
VERSION = "1.0.0"

# ================= IMPORTS =================
import os
import sys
import ctypes
import subprocess

import tkinter as tk
from tkinter import ttk, messagebox

import ipaddress
import json

"""psutil is more optimized; otherwise, we will use the netsh command."""
try:
    import psutil
except:
    psutil = None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ================= ADMIN =================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def relaunch_as_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}"', None, 1
    )


if not is_admin():
    relaunch_as_admin()
    sys.exit()


# ================= NETWORK =================

def run_netsh(args):
    return subprocess.run(["netsh"] + args, capture_output=True, text=True)


def get_interfaces():
    if not psutil:
        return []

    interfaces = []
    stats = psutil.net_if_stats()

    for name, st in stats.items():
        if not st.isup:
            continue

        lname = name.lower()

        if "loopback" in lname or lname.startswith("lo"):
            continue

        if any(v in lname for v in ["virtual", "vmware", "vbox", "docker"]):
            continue

        interfaces.append(name)

    return interfaces


def get_current_ip(interface):
    if not psutil:
        return None, None

    addrs = psutil.net_if_addrs().get(interface, [])

    for addr in addrs:
        # AF_INET = IPv4
        if str(addr.family) == "AddressFamily.AF_INET" or addr.family == 2:
            ip = addr.address
            mask = addr.netmask

            if ip and mask:
                return ip, mask

    return None, None




def set_static_ip(interface, ip, mask):
    proc = run_netsh(["interface", "ip", "set", "address", interface, "static", ip, mask])
    return proc.returncode == 0


def set_dhcp(interface):
    proc = run_netsh(["interface", "ip", "set", "address", interface, "dhcp"])
    return proc.returncode == 0


# ================= PRESETS =================

APPDATA_DIR = os.path.join(os.environ["APPDATA"], "IPSwitcher")
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
    with open(PRESET_FILE, "w") as f:
        json.dump(data, f, indent=4)


presets = load_presets()


# ================= THEME =================

BG_MAIN = "#111418"
BG_PANEL = "#1a1f26"
BG_INPUT = "#202630"
ACCENT = "#4fd1c5"
TEXT_MAIN = "#e6edf3"
TEXT_MUTED = "#9aa4af"
FONT = ("Segoe UI", 11)

root = tk.Tk()
root.update_idletasks()
root.title(f"IP Switcher v{VERSION}")
root.configure(bg=BG_MAIN)

myappid = "petitelectron.ip_switcher.v1"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

try:
    icon_img = tk.PhotoImage(file=resource_path("icon.png"))
    root.iconphoto(True, icon_img)
except tk.TclError:
    pass

"""Window config"""

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - 520) // 2
y = (screen_height - 400) // 2
root.geometry(f"520x400+{x}+{y}")

root.minsize(520, 400)
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
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=0, column=1, sticky="w")

iface_var = tk.StringVar()
iface_combo = ttk.Combobox(main_frame,
                           textvariable=iface_var,
                           state="readonly",
                           values=get_interfaces(),
                           width=70)
iface_combo.grid(row=1, column=1, sticky="w", pady=5)


tk.Label(main_frame, text="Preset",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=2, column=1, sticky="w", pady=(20, 5))

preset_var = tk.StringVar()
preset_combo = ttk.Combobox(main_frame,
                            textvariable=preset_var,
                            state="readonly",
                            values=list(presets.keys()),
                            width=70)
preset_combo.grid(row=3, column=1, sticky="w", pady=5)


tk.Label(main_frame, text="IP Address",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=4, column=1, sticky="w", pady=(15, 0))

ip_frame = tk.Frame(main_frame, bg=BG_PANEL)
ip_frame.grid(row=5, column=1, sticky="w")

ip_vars = []


tk.Label(main_frame, text="Subnet Mask",
         bg=BG_PANEL, fg=TEXT_MAIN, font=FONT).grid(row=6, column=1, sticky="w", pady=(15, 0))

mask_var = tk.StringVar()
mask_frame = tk.Frame(main_frame, bg=BG_PANEL)
mask_frame.grid(row=7, column=1, sticky="w")
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
             font=FONT).pack()

    tk.Label(win, text="Base IP (e.g. 192.168.10.0)",
             bg=BG_PANEL, fg=TEXT_MAIN,
             font=FONT).pack(pady=(15, 5))
    ip_var = tk.StringVar()
    ip_entry = tk.Entry(win,
                        textvariable=ip_var,
                        bg=BG_INPUT,
                        fg=TEXT_MAIN,
                        font=FONT)
    ip_entry.pack()

    tk.Label(win, text="Subnet Mask",
             bg=BG_PANEL, fg=TEXT_MAIN,
             font=FONT).pack(pady=(15, 5))
    mask_var_local = tk.StringVar()
    mask_entry = tk.Entry(win,
                          textvariable=mask_var_local,
                          bg=BG_INPUT,
                          fg=TEXT_MAIN,
                          font=FONT)
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

        save_presets(presets)
        preset_combo["values"] = list(presets.keys())
        messagebox.showinfo("Success", "Preset saved.")
        win.destroy()

    tk.Button(win,
              text="Confirm",
              command=confirm,
              bg=ACCENT,
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

    if messagebox.askyesno("Confirm", f"Delete preset '{preset}'?"):
        presets.pop(preset, None)
        save_presets(presets)
        preset_combo["values"] = list(presets.keys())
        preset_var.set("")
        messagebox.showinfo("Deleted", "Preset removed.")


# ================= BUTTONS =================

btn_frame = tk.Frame(main_frame, bg=BG_PANEL)
btn_frame.grid(row=8, column=1, pady=25)

tk.Button(btn_frame, text="Apply",
          command=apply,
          bg=ACCENT,
          fg="#000000",
          font=FONT,
          relief="flat",
          padx=20,
          pady=6).pack(side="left", padx=5)

tk.Button(btn_frame, text="Add Preset",
          command=add_preset,
          bg=BG_INPUT,
          fg=TEXT_MAIN,
          relief="flat",
          font=FONT).pack(side="left", padx=5)

tk.Button(btn_frame, text="Delete Preset",
          command=delete_preset,
          bg=BG_INPUT,
          fg="#ff5c5c",
          relief="flat",
          font=FONT).pack(side="left", padx=5)

# ================ EXEC ==================

iface_combo.bind("<<ComboboxSelected>>", lambda e: refresh_current())
preset_combo.bind("<<ComboboxSelected>>", on_preset_change)

root.mainloop()