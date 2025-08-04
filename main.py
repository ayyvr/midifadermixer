import os
import sys
import time
import subprocess
import threading
import configparser
import mido
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3
from PIL import Image, ImageDraw

CONFIG_PATH = os.path.expanduser("~/.config/midifadermixer/config.ini")

# Default Example Config (what I use basically,BCF2000 Faders start at CC9)
def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    else:
        config['GENERAL'] = {
            'midi_device_name': 'BCF2000 MIDI 1'
        }
        config['FADERS'] = {str(cc): "" for cc in range(18)}
        config['FADERS']['9'] = "Firefox"
        config['FADERS']['10'] = "Chromium"
        config['FADERS']['11'] = "Moonlight"
        config['FADERS']['12'] = "ALSA plug-in [java]"
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)
    return config

def save_config():
    for cc, entry in fader_entries.items():
        config['FADERS'][str(cc)] = entry.get_text()
    config['GENERAL']['midi_device_name'] = midi_device_entry.get_text()
    with open(CONFIG_PATH, 'w') as f:
        config.write(f)
    dialog = Gtk.MessageDialog(
        transient_for=window,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text="Configuration Saved",
    )
    dialog.run()
    dialog.destroy()
    reload_fader_mapping()

def parse_fader_mapping():
    mapping = {}
    for cc_str, targets in config['FADERS'].items():
        cc = int(cc_str)
        mapping[cc] = [t.strip() for t in targets.split(',') if t.strip()]
    return mapping

def reload_fader_mapping():
    global fader_mapping
    fader_mapping = parse_fader_mapping()

def get_stream_id(stream_name):
    try:
        output = subprocess.check_output(["wpctl", "status"], text=True)
        lines = output.splitlines()
        for i, line in enumerate(lines):
            if stream_name.lower() in line.lower():
                if i + 1 < len(lines) and "output" in lines[i + 1].lower():
                    return line.split()[0]
    except subprocess.CalledProcessError:
        print(f"Stream {stream_name} not found.")
    return None

def set_volume(stream_name, value):
    stream_id = get_stream_id(stream_name)
    if stream_id:
        volume = value / 127
        subprocess.run(["wpctl", "set-volume", stream_id, str(volume)])
        print(f"Set {stream_name} to {volume:.2f}")

def find_midi_input(name_hint):
    ports = mido.get_input_names()
    for port in ports:
        if name_hint.lower() in port.lower():
            return port
    print("Available MIDI ports:")
    for p in ports:
        print("  ", p)
    return None

def midi_listener():
    midi_device_name = config['GENERAL'].get('midi_device_name', 'BCF2000 MIDI 1')
    print("Looking for MIDI device...")
    port = find_midi_input(midi_device_name)
    if not port:
        print(f"No MIDI port matching '{midi_device_name}' found.")
        return
    print(f"Using MIDI port: {port}")
    try:
        midi_input = mido.open_input(port)
    except IOError as e:
        print(f"Could not open MIDI port: {e}")
        return

    while True:
        for msg in midi_input.iter_pending():
            if msg.type == "control_change" and msg.control in fader_mapping:
                for stream_name in fader_mapping[msg.control]:
                    set_volume(stream_name, msg.value)
                    GLib.idle_add(update_slider, stream_name, msg.value)
        time.sleep(0.01)

def create_icon():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill="lightblue")
    path = "/tmp/midifadermixer_icon.png"
    image.save(path)
    return path

def on_quit(_):
    Gtk.main_quit()
    sys.exit(0)

def on_show(_):
    window.present()

def update_slider(stream_name, value):
    slider = sliders.get(stream_name)
    if slider:
        slider.set_value(value)
    return False

def open_settings(_):
    window.show_all()
    window.present()

def on_slider_change(slider, stream_name):
    value = int(slider.get_value())
    set_volume(stream_name, value)

def build_window():
    global window, fader_entries, sliders, midi_device_entry

    window = Gtk.Window(title="Midi Fader Mixer")
    window.set_default_size(600, 400)
    window.connect("delete-event", lambda w,e: w.hide() or True)  # Hide on close

    grid = Gtk.Grid(column_spacing=10, row_spacing=5, margin=10)
    window.add(grid)

    fader_entries = {}
    sliders = {}

    # MIDI device name label and entry
    label_midi = Gtk.Label(label="MIDI Device Name:")
    label_midi.set_halign(Gtk.Align.START)
    grid.attach(label_midi, 0, 0, 1, 1)

    midi_device_entry = Gtk.Entry()
    midi_device_entry.set_text(config['GENERAL'].get('midi_device_name', 'BCF2000 MIDI 1'))
    grid.attach(midi_device_entry, 1, 0, 2, 1)

    # CC mappings start from row 2
    for cc in range(18):
        label = Gtk.Label(label=f"CC {cc}")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, cc + 2, 1, 1)

        entry = Gtk.Entry()
        entry.set_text(", ".join(fader_mapping.get(cc, [])))
        grid.attach(entry, 1, cc + 2, 1, 1)
        fader_entries[cc] = entry

        for stream_name in fader_mapping.get(cc, []):
            slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
            slider.set_range(0, 127)
            slider.set_value(0)
            slider.set_draw_value(False)
            slider.connect("value-changed", lambda s, name=stream_name: on_slider_change(s, name))
            grid.attach(slider, 2, cc + 2, 1, 1)
            sliders[stream_name] = slider

    save_btn = Gtk.Button(label="Save Config")
    save_btn.connect("clicked", lambda b: save_config())
    grid.attach(save_btn, 0, 20, 3, 1)

    window.show_all()
    window.hide()

def build_tray():
    global indicator

    icon_path = create_icon()
    indicator = AyatanaAppIndicator3.Indicator.new(
        "midifadermixer",
        icon_path,
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()

    item_show = Gtk.MenuItem(label="Show Mixer")
    item_show.connect("activate", on_show)
    menu.append(item_show)

    item_settings = Gtk.MenuItem(label="Settings")
    item_settings.connect("activate", open_settings)
    menu.append(item_settings)

    item_quit = Gtk.MenuItem(label="Quit")
    item_quit.connect("activate", on_quit)
    menu.append(item_quit)

    menu.show_all()
    indicator.set_menu(menu)

def main():
    global config, fader_mapping

    config = load_config()
    fader_mapping = parse_fader_mapping()

    build_window()
    build_tray()

    threading.Thread(target=midi_listener, daemon=True).start()

    Gtk.main()

if __name__ == "__main__":
    main()

