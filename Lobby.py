import arcade
import client.Client as Client
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

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")


class LobbyView(UIView):
    def __init__(self, window, client):
        super().__init__()
        self.window = window

        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        serverIP = UILabel(text="Server IP: "+client.get_server_ip(), font_size=20, text_color=arcade.color.WHITE)
        anchor = UIAnchorLayout()
        anchor.add(child=serverIP, anchor_x="left", anchor_y="top", align_x=10, align_y=-10)
        self.ui.add(anchor)

        # Central layout
        layout = UIBoxLayout(vertical=False, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))


        players = client.get_players()
        for i in range(len(players)):
            player_placeholder = GameButton(text="Player"+str(i), width=200, height=50)
            layout.add(player_placeholder)

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
        #disconnect from server
        self.window.client.disconnect()
        self.window.show_view(Mainview(self.window))

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )
if __name__ == "__main__":
    window = arcade.Window(800, 600, "Lobby", resizable=True)
    client = Client.Client()
    view = LobbyView(window, client)
    window.show_view(view)
    arcade.run()
