import arcade
from arcade.gui import UITextureButton, UITextureButtonStyle


class TankButton(UITextureButton):

    # Dictionary mapping color names to their respective textures
    TANK_TEXTURES = {
        "red": {
            "normal": ":assets:lobby_players/red.png"
        },
        "green": {
            "normal": ":assets:lobby_players/green.png"
        },
        "blue": {
            "normal": ":assets:lobby_players/blue.png"
        },
        "yellow": {
            "normal": ":assets:lobby_players/yellow.png"
        }
    }

    def set_color(self, color):
        """Change the tank color dynamically."""
        if color not in self.TANK_TEXTURES:
            color = "blue"  # Fallback to blue if invalid color

        # Load texture for the specified color
        self.texture = arcade.load_texture(self.TANK_TEXTURES[color]["normal"])

    def __init__(
            self,
            x=0,
            y=0,
            width=180,
            height=180,
            name_text="",
            font_size=16,
            font_color=(255, 255, 255, 255),
            color="blue",
            style=None,
            **kwargs
    ):
        # Validate color parameter
        if color not in self.TANK_TEXTURES:
            color = "blue"  # Fallback to blue if invalid color specified

        # Load texture for the specified color
        texture_normal = arcade.load_texture(self.TANK_TEXTURES[color]["normal"])

        # Create base style if no custom style provided
        if style is None:
            base_style = UITextureButtonStyle(
                font_name=("ARCO", "arial"),
                font_size=font_size,
                font_color=font_color
            )

            style = {
                "normal": UITextureButtonStyle(**base_style.__dict__),
                "hover": UITextureButtonStyle(**base_style.__dict__),
                "press": UITextureButtonStyle(**base_style.__dict__),
                "disabled": UITextureButtonStyle(**base_style.__dict__)
            }

        # Store the name text
        self.name_text = name_text
        self.font_size = font_size
        self.font_color = font_color

        # Call parent constructor
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            style=style,
            texture=texture_normal,
            **kwargs
        )
