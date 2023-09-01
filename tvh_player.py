import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GObject, GLib
import notify2
import time
import os
import configparser

class IPTVPlayer:
    def __init__(self):
        self.app_dir = "/tmp/iptv_player"  # Domyślny katalog aplikacji
        os.makedirs(self.app_dir, exist_ok=True)
        self.destination_dir = ""  # Początkowo pusty katalog docelowy
        self.window = Gtk.Window(title="IPTV Player")
        self.play_button = Gtk.Button(label="Play")
        self.stop_button = Gtk.Button(label="Stop")
        self.mute_button = Gtk.ToggleButton(label="Mute")
        self.filechooser_button = Gtk.Button(label="Select Playlist")
        self.playlist_store = Gtk.ListStore(str, str)
        self.playlist_combo = Gtk.ComboBox.new_with_model_and_entry(self.playlist_store)
        self.playlist_combo.set_entry_text_column(0)
        self.play_button.connect("clicked", self.on_play_button_clicked)
        self.stop_button.connect("clicked", self.on_stop_button_clicked)
        self.mute_button.connect("clicked", self.on_mute_button_clicked)
        self.filechooser_button.connect("clicked", self.on_filechooser_button_clicked)

        self.status_label = Gtk.Label(label="")
        
        self.close_button = Gtk.Button(label="Zamknij program")
        self.close_button.connect("clicked", self.on_close_button_clicked)

        self.layout = Gtk.Grid()
        self.layout.attach(self.filechooser_button, 0, 0, 3, 1)
        self.layout.attach(self.playlist_combo, 0, 1, 3, 1)
        self.layout.attach(self.play_button, 0, 2, 1, 1)
        self.layout.attach(self.stop_button, 1, 2, 1, 1)
        self.layout.attach(self.mute_button, 2, 2, 1, 1)
        self.layout.attach(self.status_label, 0, 3, 3, 1)
        self.layout.attach(self.close_button, 0, 4, 3, 1)
        self.window.add(self.layout)

        self.player = Gst.ElementFactory.make("playbin", "player")
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_bus_message)

        self.notification = notify2.init("IPTV Player")
        self.stream_start_time = None
        self.app_start_time = time.time()
        self.current_channel = ""

        self.mute_button = Gtk.ToggleButton(label="Mute")
        self.mute_button.connect("clicked", self.on_mute_button_clicked)
        self.config_file_path = os.path.join(self.app_dir, "config.ini")
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file_path):
            self.config.read(self.config_file_path)

    def on_filechooser_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Playlist", parent=self.window, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            playlist_path = dialog.get_filename()
            self.load_playlist(playlist_path)
        dialog.destroy()

    def on_play_button_clicked(self, widget):
        active_iter = self.playlist_combo.get_active_iter()
        if active_iter is not None:
            current_state = self.player.get_state(0)[1]

            if current_state == Gst.State.PAUSED:
                self.player.set_state(Gst.State.PLAYING)
                self.status_label.set_label(f"Playing: {self.current_channel}")
            elif current_state == Gst.State.PLAYING:
                self.player.set_state(Gst.State.PAUSED)
                self.status_label.set_label("Paused")
            else:
                self.player.set_state(Gst.State.NULL)
                uri = self.playlist_store[active_iter][1]
                self.player.set_property("uri", uri)
                self.player.set_state(Gst.State.PLAYING)
                self.stream_start_time = time.time()
                self.current_channel = self.playlist_store[active_iter][0]
                self.status_label.set_label(f"Playing: {self.current_channel}")
                self.show_now_playing_notification()

    def on_stop_button_clicked(self, widget):
        self.player.set_state(Gst.State.NULL)
        self.stream_start_time = None
        self.status_label.set_label("Stopped")

    def on_mute_button_clicked(self, widget):
        new_mute_state = widget.get_active()
        self.player.set_property("mute", new_mute_state)

    def get_mute_button_label(self, muted=False):
        return "Unmute" if muted else "Mute"

    def on_bus_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.stream_start_time = None
            self.status_label.set_label("End of stream")

    def show_now_playing_notification(self):
        current_time = time.strftime("%H:%M:%S")
        notification_text = f"Now Playing: {self.current_channel}\nCurrent Time: {current_time}"
        notify2.Notification("IPTV Player", notification_text, icon="dialog-information").show()


    def load_playlist(self, playlist_path):
        self.playlist_store.clear()  # Oczyść model danych ComboBoxa
        if os.path.exists(playlist_path):
            with open(playlist_path, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("#EXTINF"):
                        channel_name = line.split(",", 1)[-1].strip()
                        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        if next_line.startswith("http"):
                            self.playlist_store.append([channel_name, next_line])

    def on_close_button_clicked(self, widget):
        Gtk.main_quit()

    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    Gst.init(None)
    notify2.init("IPTV Player")
    player = IPTVPlayer()
    player.run()
