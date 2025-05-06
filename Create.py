import arcade
import socket
import threading
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
)

from pathlib import Path
from server.Server import Server
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

# Load textures and custom font
TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")
arcade.load_font(":assets:fonts/ARCO.ttf")  # <-- Load the ARCO font here

class CreateGameView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.server = None
        self.server_thread = None
        self.status_label = None

        self.background_color = arcade.color.DARK_GREEN
        self.background = arcade.load_texture(":assets:images/background.png")

        # Central layout
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Title using ARCO font
        layout.add(UILabel(
            text="Create Game",
            font_size=30,
            font_name="ARCO",  # <-- Use ARCO font here
            text_color=arcade.color.WHITE,
        ))

        # Get LAN IP
        lan_ip = self.get_lan_ip()

        # IP info label
        ip_label = UILabel(
            text=f"Your LAN IP: {lan_ip}",
            font_size=16,
            text_color=arcade.color.WHITE
        )
        layout.add(ip_label)

        # Create buttons for different server options
        btn_localhost = GameButton(text="Localhost", width=200, height=50)
        btn_localhost.on_click = self.on_localhost_click
        layout.add(btn_localhost)

        btn_lan = GameButton(text=f"LAN", color="green", width=200, height=50)
        btn_lan.on_click = self.on_lan_click
        layout.add(btn_lan)

        # Exit button in top-right corner
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

    def get_lan_ip(self):
        """Get the LAN IP address of this computer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to an external server to determine the correct interface
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost

    def on_localhost_click(self, event):
        """Start server on localhost"""
        self.start_server("127.0.0.1", 5000)
        from Lobby import LobbyView
        self.window.show_view(LobbyView(self.window, self.server, False))

    def on_lan_click(self, event):
        """Start server on LAN IP"""
        lan_ip = self.get_lan_ip()
        self.start_server(lan_ip, 5000)
        from Lobby import LobbyView
        self.window.show_view(LobbyView(self.window, self.server, False))

    def start_server(self, ip, port):
        """Start the game server in a separate thread"""
        if self.server_thread and self.server_thread.is_alive():
            return

        self.server = Server(ip=ip, port=port)

        def run_server():
            try:
                self.server.start()
            except Exception as e:
                print(f"Error: {str(e)}")

        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def on_back_click(self, event):
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )

if __name__ == "__main__":
    window = arcade.Window(title="Create Game", width=800, height=600)
    create_game_view = CreateGameView(window)
    window.show_view(create_game_view)
    arcade.run()
