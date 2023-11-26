import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk, Gst, GObject, GLib
import notify2
import time
import os
import configparser
import requests
from PIL import Image
from io import BytesIO

class IPTVPlayer:
    def __init__(self):
        self.app_dir = "/tmp/iptv_player"
        os.makedirs(self.app_dir, exist_ok=True)
        self.destination_dir = ""
        self.window = Gtk.Window(title="IPTV Player")
        self.play_button = Gtk.Button(label="Play")
        self.stop_button = Gtk.Button(label="Stop")
        self.mute_button = Gtk.ToggleButton(label="Mute")
        self.filechooser_button = Gtk.Button(label="Select Playlist")
        self.url_entry = Gtk.Entry()
        self.load_url_button = Gtk.Button(label="Load from URL")
        self.clear_playlist_button = Gtk.Button(label="Clear Playlist")
        self.url_entry.set_text("http://192.168.1.133:9981/playlist/channels.m3u")
        self.notebook = Gtk.Notebook()

        self.play_button.connect("clicked", self.on_play_button_clicked)
        self.stop_button.connect("clicked", self.on_stop_button_clicked)
        self.mute_button.connect("clicked", self.on_mute_button_clicked)
        self.filechooser_button.connect("clicked", self.on_filechooser_button_clicked)
        self.load_url_button.connect("clicked", self.on_load_url_button_clicked)
        self.clear_playlist_button.connect("clicked", self.on_clear_playlist_button_clicked)

        self.status_label = Gtk.Label(label="")

        self.copy_selected_url_button = Gtk.Button(label="Copy Selected URL")
        self.copy_selected_url_button.connect("clicked", self.on_copy_selected_url_button_clicked)

        # Create a ListStore model for the playlist
        self.playlist_model = Gtk.ListStore(str, str, str)

        # Create a TreeView with columns
        playlist_columns = ["Channel Name", "URI", "Logo URL"]
        self.playlist_treeview = Gtk.TreeView(model=self.playlist_model)
        for i, column_title in enumerate(playlist_columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.playlist_treeview.append_column(column)

        # Add the TreeView to a ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.playlist_treeview)

        # Connect row-activated signal to play the selected item
        self.playlist_treeview.connect("row-activated", self.on_playlist_row_activated)

        # Create a Box to hold the buttons and the playlist
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        button_box.pack_start(self.filechooser_button, False, False, 0)
        button_box.pack_start(self.url_entry, True, True, 0)
        button_box.pack_start(self.load_url_button, False, False, 0)
        button_box.pack_start(self.play_button, False, False, 0)
        button_box.pack_start(self.stop_button, False, False, 0)
        button_box.pack_start(self.mute_button, False, False, 0)
        button_box.pack_start(self.status_label, False, False, 0)
        button_box.pack_start(self.clear_playlist_button, False, False, 0)
        button_box.pack_start(self.copy_selected_url_button, False, False, 0)

        self.box.pack_start(button_box, False, False, 0)
        self.box.pack_start(scrolled_window, True, True, 0)

        self.close_button = Gtk.Button(label="Zamknij program")
        self.close_button.connect("clicked", self.on_close_button_clicked)
        self.box.pack_start(self.close_button, False, False, 0)

        self.window.add(self.box)

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

        self.load_saved_playlists()

    def on_copy_selected_url_button_clicked(self, widget):
        selection = self.playlist_treeview.get_selection()
        model, selected_iter = selection.get_selected()
        if selected_iter:
            playlist_url = model.get_value(selected_iter, 1)
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(playlist_url, -1)
            clipboard.store()
            print("Selected Playlist URL copied to clipboard.")

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
        active_iter = self.playlist_treeview.get_selection().get_selected()
        if active_iter:
            uri = self.playlist_model.get_value(active_iter[1], 1)
            self.player.set_property("uri", uri)
            self.player.set_state(Gst.State.PLAYING)
            self.stream_start_time = time.time()
            self.current_channel = self.playlist_model.get_value(active_iter[1], 0)
            self.status_label.set_label(f"Playing: {self.current_channel}")
            self.show_now_playing_notification()

    def on_stop_button_clicked(self, widget):
        self.player.set_state(Gst.State.NULL)
        self.stream_start_time = None
        self.status_label.set_label("Stopped")

    def on_mute_button_clicked(self, widget):
        new_mute_state = widget.get_active()
        self.player.set_property("mute", new_mute_state)

    def on_bus_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.stream_start_time = None
            self.status_label.set_label("End of stream")

    def show_now_playing_notification(self):
        current_time = time.strftime("%H:%M:%S")
        notification_text = f"Now Playing: {self.current_channel}\nCurrent Time: {current_time}"

        # Add this part to include the logo in the notification
        logo_url = self.get_logo_url_for_channel(self.current_channel)
        if logo_url:
            logo_data = requests.get(logo_url).content
            logo_image = Image.open(BytesIO(logo_data))

            # Adjust the size as needed
            logo_image = logo_image.resize((400, 200))

            logo_image_path = "/tmp/logo_image.png"  # Temporary path to save the resized image
            logo_image.save(logo_image_path)

            # Display the notification with the logo
            notification = notify2.Notification("IPTV Player", notification_text, icon=logo_image_path)
        else:
            # Display the notification without the logo if the URL is not available
            notification = notify2.Notification("IPTV Player", notification_text)

        notification.show()

    def get_logo_url_for_channel(self, channel_name):
        # Implement logic to get the logo URL for the given channel
        # This could involve searching your playlist model or using a predefined mapping
        # Replace this with your actual logic based on your playlist structure
        for row in self.playlist_model:
            if row[0] == channel_name:
                return row[2]  # Assuming the logo URL is in the third column (adjust as needed)
        return None  # Return None if the logo URL is not found

    def load_playlist(self, playlist_path):
        self.playlist_model.clear()  # Clear the existing playlist
        if os.path.exists(playlist_path):
            with open(playlist_path, "r") as f:
                lines = f.readlines()
                channel_name = ""
                logo_url = None
                for i, line in enumerate(lines):
                    if line.startswith("#EXTINF"):
                        channel_name = line.split(",", 1)[-1].strip()
                        # Extracting logo_url if available
                        if "logo=" in line:
                            logo_url = line.split("logo=")[-1].split('"')[1]
                    elif line.startswith("http"):
                        # Adding the entry to the playlist model
                        # If logo_url is None, provide an empty string as a placeholder
                        self.playlist_model.append([channel_name, line.strip(), logo_url or ""])
                        # Resetting logo_url for the next entry
                        logo_url = None

    def on_close_button_clicked(self, widget):
        self.save_playlists()
        Gtk.main_quit()

    def on_playlist_row_activated(self, treeview, path, column):
        self.on_play_button_clicked(self.play_button)

    def on_load_url_button_clicked(self, widget):
        playlist_url = self.url_entry.get_text()
        if playlist_url.startswith("http"):
            response = requests.get(playlist_url)
            if response.status_code == 200:
                playlist_content = response.text
                self.load_playlist_from_content(playlist_content)
            else:
                print(f"Failed to fetch playlist from URL. Status code: {response.status_code}")
        else:
            print("Invalid URL format")

    def on_clear_playlist_button_clicked(self, widget):
        self.playlist_model.clear()

    def save_playlists(self):
        config = configparser.ConfigParser()
        config.add_section('Playlists')
        for index, playlist in enumerate(self.get_playlist_entries()):
            config.set('Playlists', f'Playlist{index}', playlist)

        with open(self.config_file_path, 'w') as configfile:
            config.write(configfile)

    def load_saved_playlists(self):
        if os.path.exists(self.config_file_path):
            config = configparser.ConfigParser()
            config.read(self.config_file_path)

            if 'Playlists' in config:
                for key, value in config.items('Playlists'):
                    self.load_playlist(value)

    def get_playlist_entries(self):
        entries = []
        for row in self.playlist_model:
            entries.append(row[1])
        return entries

    def load_playlist_from_content(self, playlist_content):
        self.playlist_model.clear()  # Clear the existing playlist
        lines = playlist_content.splitlines()
        channel_name = ""
        logo_url = None
        for i, line in enumerate(lines):
            if line.startswith("#EXTINF"):
                channel_name = line.split(",", 1)[-1].strip()
                # Extracting logo_url if available
                if "logo=" in line:
                    logo_url = line.split("logo=")[-1].split('"')[1]
            elif line.startswith("http"):
                # Adding the entry to the playlist model
                # If logo_url is None, provide an empty string as a placeholder
                self.playlist_model.append([channel_name, line.strip(), logo_url or ""])
                # Resetting logo_url for the next entry
                logo_url = None


    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    Gst.init(None)
    notify2.init("IPTV Player")
    player = IPTVPlayer()
    player.run()
