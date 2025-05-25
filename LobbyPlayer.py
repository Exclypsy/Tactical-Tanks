import arcade
from arcade.gui import UIBoxLayout, UITextureButton, UILabel


class TankButton(UIBoxLayout):
    """A composite widget with a tank texture button and name text below."""

    # Dictionary mapping color names to their respective textures
    TANK_TEXTURES = {
        "red": ":assets:lobby_players/red.png",
        "green": ":assets:lobby_players/green.png",
        "blue": ":assets:lobby_players/blue.png",
        "yellow": ":assets:lobby_players/yellow.png"
    }

    def __init__(
            self,
            color="blue",
            name_text="",
            x=0,
            y=0,
            button_width=180,
            button_height=180,
            font_size=16,
            font_color=(255, 255, 255, 255),
            **kwargs
    ):
        super().__init__(vertical=True, space_between=5, **kwargs)

        # Validate and load texture
        if color not in self.TANK_TEXTURES:
            color = "blue"
        texture_normal = arcade.load_texture(self.TANK_TEXTURES[color])

        # Create tank button
        self.tank_button = UITextureButton(
            width=button_width,
            height=button_height,
            texture=texture_normal
        )

        # Create name label
        self.name_label = UILabel(
            text=name_text,
            font_name=("ARCO", "arial"),
            font_size=font_size,
            text_color=font_color
        )

        # Add to layout
        self.add(self.tank_button)
        self.add(self.name_label)

        self.current_color = color
        self.name_text = name_text

    def set_color(self, color):
        if color in self.TANK_TEXTURES:
            texture = arcade.load_texture(self.TANK_TEXTURES[color])
            self.tank_button.texture = texture
            self.current_color = color

    @property
    def on_click(self):
        return self.tank_button.on_click

    @on_click.setter
    def on_click(self, callback):
        self.tank_button.on_click = callback
