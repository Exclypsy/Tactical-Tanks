import threading
import arcade
import client.Client as Client
from Lobby import LobbyView
from arcade.gui import (
    UIView,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UITextureButton,
    UIInputText,
)
from pathlib import Path
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

# Load textures and custom font
TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")
arcade.load_font(":assets:fonts/ARCO.ttf")

SAVE_FILE = project_root / "last_ip.txt"  # súbor na uloženie poslednej IP

class JoinGameView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        # Connection state
        self.connecting = False
        self.error_message = None

        self.last_ip = self.load_last_ip()

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        self.main_layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[self.main_layout], anchor_x="center", anchor_y="center"))

        title_label = UILabel(
            text="Join Game",
            font_size=45,
            font_name="ARCO",
            text_color=arcade.color.WHITE
        )
        self.main_layout.add(title_label)

        ip_label = UILabel(text="IP servera:", font_size=30, text_color=arcade.color.WHITE)
        self.main_layout.add(ip_label)

        self.server_ip_input = UIInputText(
            width=200,
            height=40,
            text=self.last_ip or "127.0.0.1:5000"
        )
        self.main_layout.add(self.server_ip_input)

        self.btn_join = GameButton(text="Join Server", width=200, height=50)
        self.btn_join.on_click = self.join_server
        self.main_layout.add(self.btn_join)

        self.loading_label = UILabel(
            text="Connecting to server...",
            font_size=20,
            text_color=arcade.color.YELLOW
        )

        self.error_label = UILabel(
            text="",
            font_size=18,
            text_color=arcade.color.RED
        )

        exit_button = UITextureButton(
            texture=TEX_EXIT_BUTTON,
            texture_hovered=TEX_EXIT_BUTTON,
            texture_pressed=TEX_EXIT_BUTTON,
            width=40,
            height=40
        )
        exit_button.on_click = self.on_back_click

        anchor = UIAnchorLayout()
        anchor.add(child=exit_button, anchor_x="right", anchor_y="top", align_x=-10, align_y=-10)
        self.ui.add(anchor)

    def show_loading(self):
        self.connecting = True
        self.error_message = None

        if self.loading_label not in self.main_layout.children:
            self.main_layout.add(self.loading_label)

        if self.error_label in self.main_layout.children:
            self.main_layout.remove(self.error_label)

        self.btn_join.disabled = True

    def show_error(self, error_message):
        self.connecting = False
        self.error_message = error_message

        if self.loading_label in self.main_layout.children:
            self.main_layout.remove(self.loading_label)

        self.error_label.text = error_message
        if self.error_label not in self.main_layout.children:
            self.main_layout.add(self.error_label)

        self.btn_join.disabled = False

    def hide_status_messages(self):
        self.connecting = False
        self.error_message = None

        if self.loading_label in self.main_layout.children:
            self.main_layout.remove(self.loading_label)
        if self.error_label in self.main_layout.children:
            self.main_layout.remove(self.error_label)

        self.btn_join.disabled = False

    def join_server(self, event):
        """Handle join server button click"""
        if self.connecting:
            return  # Already connecting

        server_ip = self.server_ip_input.text.strip()
        if not server_ip:
            server_ip = "127.0.0.1:5000"

        allowed_chars = "0123456789.:"
        for char in server_ip:
            if char not in allowed_chars:
                self.show_error("Server address can only contain numbers, dots, and colons")
                return

        # Parse IP and port
        try:
            if ":" in server_ip:
                ip, port = server_ip.split(":", 1)
                ip = ip.strip() or "127.0.0.1"
                port = int(port)
            else:
                ip = server_ip
                port = 5000
        except ValueError:
            self.show_error("Invalid server address format")
            return

        self.save_last_ip(server_ip)

        self.show_loading()

        def connect_thread():
            try:
                client = Client.Client(ip, port, self.window)
                success = client.connect(timeout=8.0)

                if success:
                    arcade.schedule_once(lambda dt: self.on_connection_success(client), 0)
                else:
                    error_msg = client.get_connection_error() or "Connection failed"
                    arcade.schedule_once(lambda dt: self.on_connection_failed(error_msg), 0)

            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                arcade.schedule_once(lambda dt: self.on_connection_failed(error_msg), 0)

        threading.Thread(target=connect_thread, daemon=True).start()

    def on_connection_success(self, client):
        self.hide_status_messages()
        print("Connection successful, moving to lobby")
        self.window.show_view(LobbyView(self.window, client, True))

    def on_connection_failed(self, error_message):
        print(f"Connection failed: {error_message}")
        self.show_error(error_message)

    def on_back_click(self, event):
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )

    def save_last_ip(self, ip_text):
        try:
            with open(SAVE_FILE, "w") as f:
                f.write(ip_text)
        except Exception as e:
            print(f"Failed to save IP: {e}")

    def load_last_ip(self):
        if SAVE_FILE.exists():
            try:
                with open(SAVE_FILE, "r") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Failed to load IP: {e}")
        return ""
