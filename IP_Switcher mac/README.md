# IP Switcher – macOS Version

Lightweight utility to quickly switch IP configurations on macOS using native system tools.

---

## How it works

This version uses: networksetup


to manage network interfaces and apply IP changes.

---

## Features

- Active interface detection
- Static IP configuration
- DHCP switching
- Preset system
- Minimal UI

---

## Requirements

- macOS
- Python 3.10+
- `tkmacosx`

---

## Install (dev)

pip install tkmacosx
python3 ip_switcher_mac.py


---

## Build

pyinstaller --windowed --name "IP Switcher" --icon=icon.icns --add-data "icon.png:." ip_switcher_mac.py


---

## Notes

- The app relies on macOS system tools (`networksetup`)
- macOS may ask for permission when applying changes
- Interface names must match system names exactly

---

## Known limitations

- Limited testing across macOS versions
- Network interface detection may vary depending on hardware

---

## Preset storage

~/Library/Application Support/IPSwitcher/presets.json


---

## Contribution

Feel free to improve:

- interface detection
- UI
- network handling

---
