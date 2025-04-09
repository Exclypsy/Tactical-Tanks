from pathlib import Path

import arcade
from arcade.gui import (
    UIManager,
    UITextureButton,
    UIAnchorLayout,
    UIView, UIGridLayout,
)

project_root = Path(__file__).resolve().parent
assets_path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(assets_path.resolve()))

# Preload textures, because they are mostly used multiple times, so they are not
# loaded multiple times
TEX_RED_BUTTON_NORMAL = arcade.load_texture(":assets:butons/red_button_normal.png")
TEX_RED_BUTTON_HOVER = arcade.load_texture(":assets:butons/red_button_hover.png")
TEX_RED_BUTTON_PRESS = arcade.load_texture(":assets:butons/red_button_pressed.png")

TEX_GREEN_BUTTON_NORMAL = arcade.load_texture(":assets:butons/green_normal.png")
TEX_GREEN_BUTTON_HOVER = arcade.load_texture(":assets:butons/green_hover.png")
TEX_GREEN_BUTTON_PRESS = arcade.load_texture(":assets:butons/green_press.png")


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600


class mainview(UIView):
    """Uses the arcade.gui.UIView which takes care about the UIManager setup."""

    def __init__(self):
        super().__init__()
        # backup background color
        self.background_color = arcade.uicolor.PURPLE_AMETHYST


        self.background = arcade.load_texture(":assets:images/background.png")



        grid = UIGridLayout(
            column_count=1,
            row_count=5,
            size_hint=(0, 0),
            vertical_spacing=10,
        )

        self.ui.add(UIAnchorLayout(children=[grid]))

        # Main title (image)
        titlepath = arcade.load_texture(":assets:images/title.png")
        logoscale = 0.4
        title = arcade.gui.UIImage(texture=titlepath,width=titlepath.width*logoscale, height=titlepath.height*logoscale)

        grid.add(title, row=0, column=0)

        btn_join = UITextureButton(text="Join Game",
                                              texture=TEX_RED_BUTTON_NORMAL,
                                              texture_hovered=TEX_RED_BUTTON_HOVER,
                                              texture_pressed=TEX_RED_BUTTON_PRESS,
                                              )

        grid.add(btn_join, row=2, column=0)

        btn_create = UITextureButton(text="Create Game",
                                 texture=TEX_GREEN_BUTTON_NORMAL,
                                 texture_hovered=TEX_GREEN_BUTTON_HOVER,
                                 texture_pressed=TEX_GREEN_BUTTON_PRESS,
                                 )

        grid.add(btn_create, row=3, column=0)

        btn_settings = UITextureButton(text="Settings",
                                     texture=TEX_RED_BUTTON_NORMAL,
                                     texture_hovered=TEX_RED_BUTTON_HOVER,
                                     texture_pressed=TEX_RED_BUTTON_PRESS,
                                     )

        grid.add(btn_settings, row=4, column=0)


    def on_draw_before_ui(self):
        # Draw the background texture
        arcade.draw_texture_rect(
            self.background,arcade.LBWH(0, 0, self.width, self.height),
        )


def main():
    """ Main function """
    # Create a window class. This is what actually shows up on screen
    window = arcade.Window(title="Tactical Tank Game", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    # Show the view on screen
    window.show_view(mainview())

    # Start the arcade game loop
    arcade.run()

if __name__ == "__main__":
    main()