# IP Switcher

Minimal cross-platform utility to quickly switch IP configurations (static / DHCP) for live audio and AV network setups.

Built for real-world use in live environments where switching between networks (Dante, LA-Net, Intercom, Lighting…) needs to be fast and reliable.

---

## Features

- Interface selection (active interfaces only)
- Static IP presets
- DHCP support (e.g. Dante)
- Custom preset creation / deletion
- Presets saved locally
- Clean and minimal dark UI

---

## Platforms

### Windows

- Uses `netsh`
- Requires administrator privileges
- Presets stored in: %APPDATA%\IPSwitcher\presets.json
 
### macOS

- Uses `networksetup`
- No admin required at launch (system may prompt when applying changes)
- Presets stored in: ~/Library/Application Support/IPSwitcher/presets.json

## Download

Get the latest version here:

👉 https://github.com/PetitElectron/IP-Switcher/releases

Includes:

- Windows (.exe)
- macOS (.app)

---

## Usage

1. Select an interface
2. Choose a preset
3. Click **Apply**

---

## Presets

Default presets include:

- Dante (DHCP)
- LA-Net
- Bolero
- Art-Net
- Lighting (10.x.x.x)

You can create and delete your own presets.

---

## Development

### Windows

pip install -r requirements.txt
python ip_switcher.py


### macOS

pip install -r requirements.txt
python3 ip_switcher_mac.py


---

## Contributing

PRs welcome.

Keep code simple, readable, and practical.

---

## License

MIT
