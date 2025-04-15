import json
import arcade
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIGridLayout, UITextureButtonStyle,
)
from pathlib import Path
from SettingsWindow import save_setting, SettingsView, settings  # Importing save_setting, SettingsView, and settings
from Join import JoinGameView  # Import JoinGameView from the Join file
from Create import CreateGameView  # Import CreateGameView from the Create file
from SettingsWindow import background_music, music_player
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))
arcade.load_font(":assets:fonts/ARCO.ttf") #font load

SETTINGS_FILE = project_root / ".config" / "settings.json"

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")
MUSIC_FILE = str(path / "sounds" / "musica.mp3")
background_music = arcade.sound.load_sound(MUSIC_FILE)

def load_settings():
    """Load settings from the JSON file."""
    with open(SETTINGS_FILE, "r") as file:
        return json.load(file)


class Mainview(UIView):
    """Uses the arcade.gui.UIView which takes care about the UIManager setup."""

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.background_color = arcade.uicolor.PURPLE_AMETHYST
        self.background = arcade.load_texture(":assets:images/background.png")

        # Grid for center UI
        grid = UIGridLayout(
            column_count=1,
            row_count=5,
            size_hint=(0, 0),
            vertical_spacing=10,
        )

        self.ui.add(UIAnchorLayout(children=[grid]))

        # Title
        titlepath = arcade.load_texture(":assets:images/title.png")
        logoscale = 0.4
        title = arcade.gui.UIImage(
            texture=titlepath,
            width=titlepath.width * logoscale,
            height=titlepath.height * logoscale
        )
        grid.add(title, row=0, column=0)

        # Join button
        btn_join = GameButton(
            text="Join Game",
            width=250,
            height=70,
            style=UITextureButtonStyle(font_size=23, font_name="ARCO", font_color=(255, 255, 255, 255)),
        )

        # Open JoinGameView when the Join button is clicked
        btn_join.on_click = lambda event: self.window.show_view(JoinGameView(self.window))  # Opens JoinGameView
        grid.add(btn_join, row=2, column=0)

        # Create button
        btn_create = GameButton(
            text="Create Game",
            color="green",
            width=190,
            height=50,
        )
        # Open CreateGameView when the Create button is clicked
        btn_create.on_click = lambda event: self.window.show_view(CreateGameView(self.window))  # Opens CreateGameView
        grid.add(btn_create, row=3, column=0)

        # Settings button
        btn_settings = GameButton(
            text="Settings",
            width=190,
            height=50
        )
        btn_settings.on_click = lambda event: self.window.show_view(SettingsView(self.window))
        grid.add(btn_settings, row=4, column=0)

        # Exit button in top-right corner
        exit_button = UITextureButton(
            texture=TEX_EXIT_BUTTON,
            texture_hovered=TEX_EXIT_BUTTON,
            texture_pressed=TEX_EXIT_BUTTON,
            width=40,
            height=40
        )
        exit_button.on_click = lambda event: arcade.exit()

        anchor_layout = UIAnchorLayout()
        anchor_layout.add(
            child=exit_button,
            anchor_x="right",
            anchor_y="top",
            align_x=-10,
            align_y=-10,
        )
        self.ui.add(anchor_layout)

        global music_player
        if settings.get("music_on", True):
            if music_player and music_player.playing:
                music_player.pause()
            music_player = background_music.play(volume=settings.get("music_volume", 1.0), loop=True)

    def on_resize(self, width: int, height: int):
        """Update settings when the window is resized."""
        super().on_resize(width, height)

        # Update and save new window dimensions in the settings file
        save_setting("window_width", width)
        save_setting("window_height", height)

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )


def main():
    """ Main function """
    # Load user settings
    settings = load_settings()

    # Create a window with user-defined settings
    window = arcade.Window(
        title="Tactical Tank Game",
        fullscreen=settings["fullscreen"],
        width=settings["window_width"],
        height=settings["window_height"],
        resizable=True
    )

    # Set minimum size for the window
    window.set_minimum_size(800, 500)

    # Show the main view
    window.show_view(Mainview(window))

    # Run the application
    arcade.run()

def play_music():
    global music_player
    music_player = background_music.play(volume=settings.get("music_volume", 1.0), loop=True)

if __name__ == "__main__":
    main()
