import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from mpv import MPV
import notify2

class IPTVPlayer:
    def __init__(self):
        self.window = Gtk.Window(title="IPTV Player")
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.set_default_size(800, 600)

        self.play_button = Gtk.Button(label="Play")
        self.stop_button = Gtk.Button(label="Stop")
        self.filechooser_button = Gtk.Button(label="Select Playlist")
        self.playlist_store = Gtk.ListStore(str, str)
        self.playlist_combo = Gtk.ComboBox.new_with_model_and_entry(self.playlist_store)
        self.playlist_combo.set_entry_text_column(0)

        self.play_button.connect("clicked", self.on_play_button_clicked)
        self.stop_button.connect("clicked", self.on_stop_button_clicked)
        self.filechooser_button.connect("clicked", self.on_filechooser_button_clicked)

        self.layout = Gtk.Grid()
        self.layout.attach(self.filechooser_button, 0, 0, 3, 1)
        self.layout.attach(self.playlist_combo, 0, 1, 3, 1)
        self.layout.attach(self.play_button, 0, 2, 1, 1)
        self.layout.attach(self.stop_button, 2, 2, 1, 1)
        self.window.add(self.layout)

        self.player = MPV()
        self.notification = notify2.init("IPTV Player")

    def populate_playlist(self, playlist_path):
        with open(playlist_path, 'r') as playlist_file:
            name = None
            for line in playlist_file:
                line = line.strip()
                if line.startswith("#EXTINF:-1"):
                    name = line.split(',')[-1].strip()
                elif name is not None and line:
                    self.playlist_store.append([name, line])
                    name = None

    def on_play_button_clicked(self, widget):
        active_iter = self.playlist_combo.get_active_iter()
        if active_iter is not None:
            playlist_item = self.playlist_store[active_iter][0]
            uri = self.playlist_store[active_iter][1]
            if uri:
                self.player.play(uri)
                self.show_notification(f"Playing {playlist_item}", uri)

    def on_stop_button_clicked(self, widget):
        self.player.stop()

    def on_filechooser_button_clicked(self, widget):
        filechooser = Gtk.FileChooserDialog(
            title="Select IPTV Playlist", parent=self.window, action=Gtk.FileChooserAction.OPEN
        )
        filechooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            self.playlist_path = filechooser.get_filename()
            self.populate_playlist(self.playlist_path)
        filechooser.destroy()

    def show_notification(self, message, link):
        notify2.Notification("IPTV Player", message, icon="dialog-information").show()
        notify2.Notification("Link to Play", link, icon="dialog-information").show()

    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    notify2.init("IPTV Player")
    player = IPTVPlayer()
    player.run()

