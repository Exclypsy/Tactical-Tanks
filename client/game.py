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

    def toggle_pause_menu(self, event=None):  # Accept the event argument
        if self.popup_active:
            self.manager.remove(self.popup_box)
            self.popup_active = False
        else:
            # Make the layout of the pause menu 2 times bigger
            layout = UIBoxLayout(vertical=True, space_between=50)  # Increased space between elements
            layout.with_background(color=(0, 0, 0, 200))  # translucent background

            # Resume button (size doubled)
            resume_btn = UIFlatButton(text="Resume", width=500)  # Bigger button
            @resume_btn.event("on_click")
            def resume_click(event):
                self.toggle_pause_menu()

            # Exit button (size doubled)
            exit_btn = UIFlatButton(text="Exit to Menu", width=500)  # Bigger button
            @exit_btn.event("on_click")
            def exit_click(event):
                self.on_back_click(None)

            # Volume slider
            volume_label = UILabel(text="Volume", width=500)  # Increased width of label
            self.volume_slider = UISlider(min=0, max=1, value=0.5, width=500)  # Larger slider
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
