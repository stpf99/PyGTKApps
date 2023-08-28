import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst

class MusicPlayer:
    def __init__(self):
        self.window = Gtk.Window(title="Music Player")
        self.window.connect("destroy", Gtk.main_quit)

        self.playbin = Gst.ElementFactory.make("playbin", "playbin")
        self.playing = False

        self.liststore = Gtk.ListStore(str)
        self.treeview = Gtk.TreeView.new_with_model(self.liststore)
        self.treeview.set_rules_hint(True)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.treeview.append_column(column)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.treeview)

        self.play_button = Gtk.Button(label="Play")
        self.play_button.connect("clicked", self.toggle_playback)

        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.stop_playback)

        self.load_button = Gtk.Button(label="Load Music")
        self.load_button.connect("clicked", self.load_music)

        self.hbox = Gtk.Box(spacing=6)
        self.hbox.pack_start(self.play_button, False, False, 0)
        self.hbox.pack_start(self.stop_button, False, False, 0)
        self.hbox.pack_start(self.load_button, False, False, 0)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vbox.pack_start(scrolled_window, True, True, 0)
        self.vbox.pack_start(self.hbox, False, False, 0)

        self.window.add(self.vbox)
        self.window.show_all()

        self.folder_path = None  # Initialize folder_path

    def load_music(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose a folder", self.window, Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK)
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.folder_path = dialog.get_filename()
            dialog.destroy()
            self.populate_playlist(self.folder_path)
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def populate_playlist(self, folder_path):
        self.liststore.clear()
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mp3', '.ogg', '.flac')):
                    self.liststore.append([file])

    def toggle_playback(self, widget):
        if not self.playing:
            selection = self.treeview.get_selection()
            model, treeiter = selection.get_selected()
            if treeiter is not None and self.folder_path is not None:
                filepath = os.path.join(self.folder_path, model[treeiter][0])
                self.playbin.set_property("uri", "file://" + filepath)
                self.playbin.set_state(Gst.State.PLAYING)
                self.playing = True
        else:
            self.playbin.set_state(Gst.State.NULL)
            self.playing = False

    def stop_playback(self, widget):
        self.playbin.set_state(Gst.State.NULL)
        self.playing = False

if __name__ == "__main__":
    Gst.init(None)
    player = MusicPlayer()
    Gtk.main()

