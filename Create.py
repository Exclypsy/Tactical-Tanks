import json
import arcade
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UIFlatButton,
)

from pathlib import Path

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")


class CreateGameView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.background_color = arcade.color.DARK_GREEN

        # Central layout
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Title
        layout.add(UILabel(text="Create Game", font_size=30, text_color=arcade.color.WHITE))

        # Game settings could be added here

        # Create button
        btn_create = UIFlatButton(text="Create Server", width=200, height=50)
        # btn_create.on_click = self.on_create_server
        layout.add(btn_create)


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