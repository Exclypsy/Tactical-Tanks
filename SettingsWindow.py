import json
import arcade
import arcade.sound
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UIFlatButton,
)

from pathlib import Path

from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

SETTINGS_FILE = project_root / ".config" / "settings.json"

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")
MUSIC_FILE = str(path / "sounds" / "musica.mp3")
background_music = arcade.sound.load_sound(MUSIC_FILE)
music_player = None

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

# read "fullscreen" setting from settings.json once
is_fullscreen = settings.get("fullscreen", False)

class SettingsView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.background_color = arcade.color.DARK_SLATE_GRAY

        self.background = arcade.load_texture(":assets:images/background.png")

        # Stredové rozloženie
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Nadpis
        layout.add(UILabel(text="Settings", font_size=30, text_color=arcade.color.WHITE))

        # Výber režimu zobrazenia
        self.display_mode = "fullscreen"  # Default
        self.music_on = settings.get("music_on", True)
        self.music_volume = settings.get("music_volume", 1.0)

        def set_display_mode(mode):
            self.display_mode = mode
            if mode == "fullscreen":
                self.window.set_fullscreen(True)
                is_fullscreen = True
                save_setting("fullscreen", True)
            elif mode == "windowed":
                self.window.set_fullscreen(False)
                is_fullscreen = False
                save_setting("fullscreen", False)

        btn_fullscreen = GameButton(color="red" if is_fullscreen else "green", text="Fullscreen", width=200, height=50)
        btn_fullscreen.on_click = lambda event: set_display_mode("fullscreen")

        btn_windowed = GameButton(color="green" if is_fullscreen else "red", text="Windowed", width=200, height=50)
        btn_windowed.on_click = lambda event: set_display_mode("windowed")

        layout.add(btn_fullscreen)
        layout.add(btn_windowed)

        def toggle_music():
            global music_player
            self.music_on = not self.music_on
            save_setting("music_on", self.music_on)  # Uloženie stavu hudby
            if self.music_on:
                if not music_player or not music_player.playing:
                    music_player = background_music.play(volume=self.music_volume, loop=True)
            else:
                if music_player:
                    music_player.stop()
                    music_player = None

        def set_volume(value):
            global music_player
            self.music_volume = value
            save_setting("music_volume", value)  # Uloženie hlasitosti
            if music_player:
                music_player.volume = value

        music_toggle = GameButton(text="Music: On" if self.music_on else "Music: Off", width=200, height=50)
        music_toggle.on_click = lambda event: [toggle_music(), setattr(music_toggle, 'text', "Music: On" if self.music_on else "Music: Off")]

        layout.add(music_toggle)

        from arcade.gui import UISlider
        volume_slider = UISlider(value=self.music_volume, min_value=0.0, max_value=1.0, width=200)
        volume_slider.on_change = lambda value: set_volume(value)
        layout.add(volume_slider)

        # Tlačidlo späť v pravom hornom rohu
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