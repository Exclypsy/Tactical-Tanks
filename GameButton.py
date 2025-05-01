import arcade
from arcade.gui import UITextureButton, UITextureButtonStyle


class GameButton(UITextureButton):
    """A UITextureButton that uses ARCO font by default with color selection."""

    # Dictionary mapping color names to their respective textures
    BUTTON_TEXTURES = {
        "red": {
            "normal": ":assets:buttons/red_normal.png",
            "hover": ":assets:buttons/red_hover.png",
            "press": ":assets:buttons/red_normal.png"
        },
        "green": {
            "normal": ":assets:buttons/green_normal.png",
            "hover": ":assets:buttons/green_hover.png",
            "press": ":assets:buttons/green_normal.png"
        }
        # You can add more colors as needed
    }

    def set_color(self, color):
        """Change the button color dynamically."""
        if color not in self.BUTTON_TEXTURES:
            color = "red"  # Fallback to red if invalid color

        # Load textures for the specified color
        self.texture = arcade.load_texture(self.BUTTON_TEXTURES[color]["normal"])
        self.texture_hovered = arcade.load_texture(self.BUTTON_TEXTURES[color]["hover"])
        self.texture_pressed = arcade.load_texture(self.BUTTON_TEXTURES[color]["press"])

    def __init__(
            self,
            x=0,
            y=0,
            width=190,
            height=50,
            text="",
            font_size=14,
            font_color=(255, 255, 255, 255),
            color="red",
            style=None,
            **kwargs
    ):
        # Validate color parameter
        if color not in self.BUTTON_TEXTURES:
            color = "red"  # Fallback to red if invalid color specified

        # Load textures for the specified color
        texture_normal = arcade.load_texture(self.BUTTON_TEXTURES[color]["normal"])
        texture_hover = arcade.load_texture(self.BUTTON_TEXTURES[color]["hover"])
        texture_press = arcade.load_texture(self.BUTTON_TEXTURES[color]["press"])

        # Convert style if it's a single UITextureButtonStyle object
        if isinstance(style, UITextureButtonStyle):
            style_dict = {
                "normal": UITextureButtonStyle(**vars(style)),
                "hover": UITextureButtonStyle(**vars(style)),
                "press": UITextureButtonStyle(**vars(style)),
                "disabled": UITextureButtonStyle(**vars(style))
            }
            style = style_dict
        # Create base style if no custom style provided
        elif style is None:
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

        # Call parent constructor with appropriate textures based on color
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            text=text,
            style=style,
            texture=texture_normal,
            texture_hovered=texture_hover,
            texture_pressed=texture_press,
            **kwargs
        )
