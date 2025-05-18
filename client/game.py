import json
from pathlib import Path
import random

import arcade
from arcade.gui import (
    UIManager, UITextureButton, UIAnchorLayout,
    UIFlatButton, UIBoxLayout, UILabel, UISlider
)

from client.Tank import Tank
from client.Tree import Tree

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
        self.other_player_tanks = {}
        self.available_colors = ["blue", "red", "yellow", "green"]

        player_id = "host" if not is_client else self.client_or_server.player_name
        tank_color = random.choice(self.available_colors)
        self.available_colors.remove(tank_color)

        self.player_tank = Tank(tank_color=tank_color, player_id=player_id)
        self.player_tank.center_x = self.width // 2
        self.player_tank.center_y = self.height // 2
        self.player_tank.is_rotating = True
        self.tanks.append(self.player_tank)


        arcade.schedule(self.send_tank_update, 1 / 60)
        arcade.schedule(self.process_queued_tank_updates, 1 / 60)

        # # Trees
        # self.trees = arcade.SpriteList()
        # for _ in range(random.randint(3, 7)):
        #     tree = Tree()
        #     self.trees.append(tree)

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
            self.volume_slider = UISlider(min=0, max=1, value=0.5, width=400)

            layout.add(volume_label)
            layout.add(self.volume_slider)
            layout.add(resume_btn)
            layout.add(exit_btn)

            background_box = UIAnchorLayout()
            background_box.with_background(color=(0, 0, 0, 200))
            background_box.add(child=layout, anchor_x="center", anchor_y="center")

            self.popup_box = background_box
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
        # self.trees.draw()
        for tank in self.tanks:
            tank.bullet_list.draw()
        self.tanks.draw()

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
            # for tree in self.trees:
            #     tree.update(tank.bullet_list)
            hit_tank = tank.check_bullet_collisions([t for t in self.tanks if t != tank])
            if hit_tank and hit_tank == self.player_tank and hit_tank.destroyed:
                self.game_over = True

    def on_back_click(self, event):

        arcade.unschedule(self.send_tank_update)
        arcade.unschedule(self.process_queued_tank_updates)

        self.manager.disable()
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))
        if self.is_client:
            self.client_or_server.disconnect()
        else:
            self.client_or_server.shutdown()
        self.client_or_server = None

    def process_queued_tank_updates(self, delta_time=None):
        """Process any queued tank updates from the networking thread"""
        if not self.client_or_server:
            return

        updates_to_process = []

        # Safely get pending updates
        if hasattr(self.client_or_server, 'pending_tank_updates'):
            with self.client_or_server.tank_updates_lock:
                updates_to_process = self.client_or_server.pending_tank_updates.copy()
                self.client_or_server.pending_tank_updates.clear()

        # Process each update in the main thread
        for update in updates_to_process:
            self.process_tank_update(update)

    def send_tank_update(self, delta_time=None):
        """Send player tank state to server/clients"""
        if self.game_over or self.popup_active or not self.client_or_server:
            return

        tank_data = {
            "type": "tank_state",
            "player_id": self.player_tank.player_id,
            "x": self.player_tank.center_x,
            "y": self.player_tank.center_y,
            "angle": self.player_tank.angle,
            "is_rotating": self.player_tank.is_rotating,
            "is_moving": self.player_tank.is_moving,
            "tank_color": self.player_tank.tank_color
        }

        if self.is_client:
            self.client_or_server.game_send_my_state(tank_data)
        else:
            self.client_or_server.game_broadcast_data(tank_data)

    def process_tank_update(self, data):
        """Handle received tank state update"""
        player_id = data.get("player_id")

        # Skip our own tank
        if player_id == self.player_tank.player_id:
            return

        # Print player IDs for debugging
        print(f"Game -> 258: Processing tank update: {player_id} (our ID: {self.player_tank.player_id})")

        # Create or update the tank for this player
        if player_id not in self.other_player_tanks:
            print(f"Creating new tank for player: {player_id}")
            tank_color = data.get("tank_color", "blue")

            new_tank = Tank(tank_color=tank_color, player_id=player_id)
            self.other_player_tanks[player_id] = new_tank
            self.tanks.append(new_tank)

        # Update tank state
        tank = self.other_player_tanks[player_id]
        tank.center_x = data.get("x", tank.center_x)
        tank.center_y = data.get("y", tank.center_y)
        tank.angle = data.get("angle", tank.angle)
        tank.is_rotating = data.get("is_rotating", tank.is_rotating)
        tank.is_moving = data.get("is_moving", tank.is_moving)