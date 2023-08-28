import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gst

Gst.init(None)

class IPTVPlayer:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_title("IPTV M3U Video Streaming Player")
        self.window.connect("destroy", self.quit)

        self.playing = False
        self.playbin = Gst.ElementFactory.make("playbin", "playbin")

        self.play_button = Gtk.Button(label="Play")
        self.play_button.connect("clicked", self.toggle_play)
        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.stop)
        self.load_button = Gtk.Button(label="Load M3U")
        self.load_button.connect("clicked", self.load_m3u)

        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.controls_box.pack_start(self.play_button, False, False, 0)
        self.controls_box.pack_start(self.stop_button, False, False, 0)
        self.controls_box.pack_start(self.load_button, False, False, 0)

        self.playlist_store = Gtk.ListStore(str, str)
        self.playlist_view = Gtk.TreeView(model=self.playlist_store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Playlist", renderer, text=0)
        self.playlist_view.append_column(column)
        self.playlist_view.connect("row-activated", self.on_playlist_row_activated)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.playlist_view)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.main_box.pack_start(self.controls_box, False, False, 0)
        self.main_box.pack_start(scrolled_window, True, True, 0)

        self.window.add(self.main_box)
        self.window.show_all()

        self.update_handler = GObject.timeout_add(1000, self.update_playlist)

    def toggle_play(self, widget):
        if not self.playing:
            uri = self.get_selected_uri()
            if uri:
                self.playbin.set_property("uri", uri)
                self.playbin.set_state(Gst.State.PLAYING)
                self.playing = True
                self.play_button.set_label("Pause")
        else:
            self.playbin.set_state(Gst.State.PAUSED)
            self.playing = False
            self.play_button.set_label("Play")

    def stop(self, widget):
        self.playbin.set_state(Gst.State.NULL)
        self.playing = False
        self.play_button.set_label("Play")

    def load_m3u(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose an M3U file", self.window,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.load_playlist(filename)
        dialog.destroy()


    def load_playlist(self, filename):
        self.playlist_store.clear()
        with open(filename, "r") as f:
            channel_name = ""
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF:-1"):
                    channel_name = line.split(",")[-1]
                elif line and not line.startswith("#"):
                    self.playlist_store.append([channel_name, line])
                    channel_name = ""

    def get_selected_uri(self):
        selection = self.playlist_view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            return model[treeiter][1]
        return None

    def update_playlist(self):
        # Aktualizacja listy playlisty (jeśli potrzebne)
        return True

    def quit(self, widget):
        self.mpv_player.terminate()
        Gtk.main_quit()

    def on_playlist_row_activated(self, treeview, path, column):
        self.toggle_play(None)

if __name__ == "__main__":
    IPTVPlayer()
    GObject.threads_init()
    Gtk.main()


