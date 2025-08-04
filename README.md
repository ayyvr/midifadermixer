Midi Fader Mixer

Midi Fader Mixer is a simple MIDI-controlled audio volume mixer for PipeWire streams. It supports mapping MIDI CC faders to named audio streams and allows volume control via a GTK GUI and system tray icon compatible with Wayland (wlroots/Waybar).
Features

    Map up to 18 MIDI CC channels to audio stream names

    Customizable MIDI device name (default: BCF2000 MIDI 1)

    GTK3-based GUI with sliders and text entry for stream names

    System tray indicator using Ayatana AppIndicator for Wayland support

    Saves and loads configuration from ~/.config/midifadermixer/config.ini

Requirements

    Python 3

    Python packages:

        mido

        python-gi (PyGObject)

        Pillow

    PipeWire and wpctl command line utility

    MIDI device connected and recognized by the system

    GTK3 and Ayatana AppIndicator3 libraries installed on your system

Installation (Fedora example)

sudo dnf install python3-mido python3-gobject python3-pillow pipewire-tools gtk3 libayatana-appindicator3

Usage

Run the main script:

python3 midifadermixer.py

The GUI starts with the MIDI device name set to BCF2000 MIDI 1 by default. You can change it if needed. MIDI CC numbers 0-17 can be mapped to audio stream names. Use the sliders or your MIDI controller faders to adjust volumes.

The tray icon lets you show/hide the mixer window or quit the application.
Configuration

Settings are saved in ~/.config/midifadermixer/config.ini. You can edit this file manually to adjust MIDI device name or fader mappings.
