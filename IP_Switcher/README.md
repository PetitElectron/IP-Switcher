# IP Switcher

Minimal Windows utility to quickly switch IP configurations (static/DHCP) for live audio / stage network setups.

# Features
- Interface selection (filters active adapters)
- Static IP presets
- DHCP preset (like Dante)
- Custom preset creation / deletion
- Presets stored in `%APPDATA%/IPSwitcher/presets.json`
- Dark, minimal UI

# Requirements
- Windows 10/11
- Python 3.10+ (recommanded)
- Administrator privileges (the app relaunches as admin)

# Install
```bash
pip install -r requirements.txt
python ip_switcher.py
```
# Download

A packaged Windows executable is available in the Releases section.

# Presets

Actual presets are saved to:
%APPDATA%\IPSwitcher\presets.json

# Contributing

PRs welcome. Keep changes minimal and readable.

# License

MIT
