import arcade
from arcade.gui import (
    UIView,
    UITextureButton,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UISpace,
    UIFlatButton,
)

from pathlib import Path

# Register resource handle
project_root = Path(__file__).resolve().parent
assets_path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(assets_path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")

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
            elif mode == "windowed":
                self.window.set_fullscreen(False)

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
        from main import mainview
        self.window.show_view(mainview(self.window))
