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

SETTINGS_FILE = project_root / ".config" / "settings.json"

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")

def save_setting(key, value):
    settings = {}
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
    settings[key] = value
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)



class SettingsView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.background_color = arcade.color.DARK_SLATE_GRAY

        # Stredové rozloženie
        layout = UIBoxLayout(vertical=True, space_between=20)
        self.ui.add(UIAnchorLayout(children=[layout], anchor_x="center", anchor_y="center"))

        # Nadpis
        layout.add(UILabel(text="Settings", font_size=30, text_color=arcade.color.WHITE))

        # Výber režimu zobrazenia
        self.display_mode = "fullscreen"  # Default

        def set_display_mode(mode):
            self.display_mode = mode
            if mode == "fullscreen":
                self.window.set_fullscreen(True)
                save_setting("fullscreen", True)
            elif mode == "windowed":
                self.window.set_fullscreen(False)
                save_setting("fullscreen", False)

        btn_fullscreen = UIFlatButton(text="Fullscreen", width=200, height=50)
        btn_fullscreen.on_click = lambda event: set_display_mode("fullscreen")

        btn_windowed = UIFlatButton(text="Windowed", width=200, height=50)
        btn_windowed.on_click = lambda event: set_display_mode("windowed")

        layout.add(btn_fullscreen)
        layout.add(btn_windowed)

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
        from MainMenu import mainview
        self.window.show_view(mainview(self.window))