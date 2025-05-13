import json
from pathlib import Path
import random

import arcade
from arcade.gui import (
    UIManager, UITextureButton, UIAnchorLayout,
    UIFlatButton, UIBoxLayout, UILabel, UISlider
)

from client.Tank import Tank
from client.tree import Tree

project_root = Path(__file__).resolve().parent.parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")

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

# Default player name if not set
player_name = settings.get("player_name", "Player")


class GameView(arcade.View):
    def __init__(self, window, client_or_server, is_client):
        super().__init__()
        self.window = window
        self.background = arcade.Sprite(":assets:images/forestBG.jpg")
        self.background.center_x = self.window.width // 2
        self.background.center_y = self.window.height // 2

        self.client_or_server = client_or_server
        self.is_client = is_client

        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Tanks
        self.tanks = arcade.SpriteList()
        self.player_tank = Tank(player_id="player1")
        self.player_tank.center_x = self.width // 2
        self.player_tank.center_y = self.height // 2
        self.player_tank.is_rotating = True
        self.tanks.append(self.player_tank)

        # Trees
        self.trees = arcade.SpriteList()
        for _ in range(random.randint(3, 7)):
            tree = Tree()
            self.trees.append(tree)

        # UI
        self.manager = UIManager()
        self.manager.enable()

        # Exit button (make it smaller)
        exit_button = UITextureButton(
            texture=TEX_EXIT_BUTTON,
            texture_hovered=TEX_EXIT_BUTTON,
            texture_pressed=TEX_EXIT_BUTTON,
            width=60,  # Smaller button
            height=60  # Smaller button
        )
        exit_button.on_click = self.toggle_pause_menu  # Open the pause menu instead of exiting
        anchor = UIAnchorLayout()
        anchor.add(child=exit_button, anchor_x="right", anchor_y="top", align_x=-10, align_y=-10)
        self.manager.add(anchor)

        # Debug
        self.show_hitboxes = False
        self.game_over = False

        # Pause menu support
        self.popup_active = False
        self.popup_box = None
        self.volume_slider = None

    def toggle_pause_menu(self, event=None):
        if self.popup_active:
            self.manager.remove(self.popup_box)
            self.popup_active = False
        else:
            layout = UIBoxLayout(vertical=True, space_between=50)
            layout.with_background(color=(0, 0, 0, 200))

            def create_textured_button(text, click_handler):
                normal_texture = arcade.load_texture(":assets:buttons/green_normal.png")
                hover_texture = arcade.load_texture(":assets:buttons/green_hover.png")

                button = UITextureButton(
                    texture=normal_texture,
                    texture_hovered=hover_texture,
                    texture_pressed=normal_texture,
                    width=300,
                    height=75
                )

                label = UILabel(text=text, text_color=arcade.color.WHITE, font_size=18, bold=True)
                box = UIBoxLayout(vertical=True, align="center")
                box.add(label)
                button.add(box)

                button.on_click = click_handler
                return button

            resume_btn = create_textured_button("Resume", lambda e: self.toggle_pause_menu())
            exit_btn = create_textured_button("Exit to Menu", lambda e: self.on_back_click(None))

            volume_label = UILabel(text="Volume", width=500)
            self.volume_slider = UISlider(min=0, max=1, value=0.5, width=500)

            layout.add(volume_label)
            layout.add(self.volume_slider)
            layout.add(resume_btn)
            layout.add(exit_btn)

            self.popup_box = UIAnchorLayout()
            self.popup_box.add(child=layout, anchor_x="center", anchor_y="center")
            self.manager.add(self.popup_box)
            self.popup_active = True

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.player_tank.center_x = width // 2
        self.player_tank.center_y = height // 2
        self.background.center_x = width // 2
        self.background.center_y = height // 2

    def on_draw(self):
        self.clear()
        arcade.draw_sprite(self.background)
        self.trees.draw()
        for tank in self.tanks:
            tank.bullet_list.draw()
        self.tanks.draw()
        self.player_tank.draw_debug_direction_line(self.width, self.height)

        if self.show_hitboxes:
            for tank in self.tanks:
                tank.bullet_list.draw_hit_boxes(arcade.color.RED)
            self.tanks.draw_hit_boxes(arcade.color.GREEN)

        if self.game_over:
            arcade.draw_text("GAME OVER - TANK DESTROYED!",
                             self.width / 2, self.height / 2,
                             arcade.color.RED, 24, anchor_x="center")

        self.manager.draw()

    def on_key_press(self, key, modifiers):
        if self.game_over:
            return
        if key == arcade.key.SPACE:
            self.player_tank.handle_key_press(key)
        elif key == arcade.key.H:
            self.show_hitboxes = not self.show_hitboxes
        elif key == arcade.key.ESCAPE:
            self.toggle_pause_menu()

    def on_key_release(self, key, modifiers):
        if not self.game_over and key == arcade.key.SPACE:
            self.player_tank.handle_key_release(key)

    def on_update(self, delta_time):
        if self.game_over or self.popup_active:
            return

        for tank in self.tanks:
            tank.update(delta_time, self.width, self.height)
            for tree in self.trees:
                tree.update(tank.bullet_list)
            hit_tank = tank.check_bullet_collisions([t for t in self.tanks if t != tank])
            if hit_tank and hit_tank == self.player_tank and hit_tank.destroyed:
                self.game_over = True

    def on_back_click(self, event):
        self.manager.disable()
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))
        if self.is_client:
            self.client_or_server.disconnect()
        else:
            self.client_or_server.shutdown()
        self.client_or_server = None
