import json
import arcade
import arcade.sound
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UIInputText,
    UISlider,
)
from pathlib import Path
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

# Load textures and sounds
TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")
arcade.load_font(":assets:fonts/ARCO.ttf")  # Load ARCO font
MUSIC_FILE = str(path / "sounds" / "musica.mp3")
background_music = arcade.sound.load_sound(MUSIC_FILE)
music_player = None

# Load settings
SETTINGS_FILE = project_root / ".config" / "settings.json"
settings = {}
try:
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
except json.JSONDecodeError:
    print("⚠️ Nastal problém pri načítaní settings.json – používa sa prázdne nastavenie.")
    settings = {}

def save_setting(key, value):
    settings[key] = value
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

is_fullscreen = settings.get("fullscreen", False)


def toggle_fullscreen(window_self, fullscreen_button=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    window_self.set_fullscreen(is_fullscreen)
    save_setting("fullscreen", is_fullscreen)
    if fullscreen_button:
        fullscreen_button.text = "Fullscreen: ON" if is_fullscreen else "Fullscreen: OFF"
        fullscreen_button.set_color("green" if is_fullscreen else "red")

class SettingsView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.background_color = arcade.color.DARK_SLATE_GRAY
        self.background = arcade.load_texture(":assets:images/background.png")

        # Title label with ARCO font
        anchor = UIAnchorLayout()
        anchor.add(
            child=UILabel(
                text="Settings",
                font_size=30,
                font_name="ARCO",  # ARCO font applied
                text_color=arcade.color.WHITE
            ),
            anchor_x="center",
            anchor_y="top",
            align_y=-10
        )
        self.ui.add(anchor)

        # Main layout
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Profile section
        layout.add(UILabel(text="Profile", font_size=20, text_color=arcade.color.LIGHT_GRAY))
        layout.add(UIBoxLayout(vertical=True, space_between=10))

        self.player_name = settings.get("player_name", "Player")
        name_row = UIBoxLayout(horizontal=True, space_between=10)
        self.name_input = UIInputText(text=self.player_name, width=300, height=40, font_size=20)
        name_row.add(self.name_input)

        def on_name_change(event):
            self.player_name = event.source.text
        self.name_input.on_change = on_name_change

        def on_save_click(event):
            new_name = self.name_input.text.strip() or "Player"
            self.player_name = new_name
            self.name_input.text = new_name
            save_setting("player_name", new_name)

        save_button = GameButton(text="Save", width=120, height=40)
        save_button.on_click = on_save_click
        name_row.add(save_button)
        layout.add(name_row)

        # Screen mode section
        self.music_on = settings.get("music_on", True)
        self.music_volume = settings.get("music_volume", 1.0)

        layout.add(UILabel(text="Screen", font_size=20, text_color=arcade.color.LIGHT_GRAY))
        fullscreen_button = GameButton(
            text="Fullscreen: ON" if is_fullscreen else "Fullscreen: OFF",
            width=200,
            height=50,
            color="green" if is_fullscreen else "red"
        )


        fullscreen_button.on_click = lambda event: toggle_fullscreen(self.window, fullscreen_button)
        layout.add(fullscreen_button)

        # Music section
        layout.add(UILabel(text="Music FS/SX", font_size=20, text_color=arcade.color.LIGHT_GRAY))

        def toggle_music():
            global music_player
            if music_player and music_player.playing:
                music_player.pause()
                music_player = None
            self.music_on = not self.music_on
            save_setting("music_on", self.music_on)
            if self.music_on:
                music_player = background_music.play(volume=self.music_volume, loop=True)

        music_toggle = GameButton(
            text="Music: ON" if self.music_on else "Music: OFF",
            width=200,
            height=50
        )

        def update_music_toggle():
            music_toggle.text = "Music: ON" if self.music_on else "Music: OFF"
            music_toggle.set_color("green" if self.music_on else "red")

        music_toggle.on_click = lambda event: (toggle_music(), update_music_toggle())
        layout.add(music_toggle)

        volume_slider = UISlider(value=self.music_volume, min_value=0.0, max_value=1.0, width=200)
        volume_slider.on_change = lambda event: self.set_volume(event.source.value)
        layout.add(volume_slider)

        # Exit button
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

    def set_volume(self, value):
        self.music_volume = value
        save_setting("music_volume", value)
        if music_player:
            music_player.volume = value

    def on_back_click(self, event):
        name = self.name_input.text.strip() or "Player"
        self.player_name = name
        self.name_input.text = name
        save_setting("player_name", name)
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )
