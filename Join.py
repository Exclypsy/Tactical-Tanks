import arcade
import client.Client as Client
from Lobby import LobbyView
from arcade.gui import (
    UIView,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UITextureButton,
    UIInputText,  # Import UIInputText
)
from pathlib import Path
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")


class JoinGameView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        # Central layout
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Title
        layout.add(UILabel(text="Join Game", font_size=45, text_color=arcade.color.WHITE))

        layout.add(UILabel(text="IP servera:", font_size=30, text_color=arcade.color.WHITE))

        # Server IP input field
        self.server_ip_input = UIInputText(width=200, height=40, text="")
        layout.add(self.server_ip_input)

        # Join button
        btn_join = GameButton(text="Join Server", width=200, height=50)
        btn_join.on_click = self.join_server
        layout.add(btn_join)

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

    def on_back_click(self, event):
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )

    def join_server(self, event):
        server_ip = self.server_ip_input.text
        if not server_ip:
            print("Defaulting to localhost")
            server_ip="127.0.0.1:5000"
        ip = server_ip.split(":")[0]
        port = server_ip.split(":")[1]

        client = Client.Client(ip, port, self.window)
        client.connect()  # Just connect

        if client.connected:
            self.window.show_view(LobbyView(self.window, client, True))
        else:
            print("Error connecting")


if __name__ == "__main__":
    window = arcade.Window(800, 600, "Join Game View")
    view = JoinGameView(window)
    window.show_view(view)
    arcade.run()