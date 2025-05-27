import json
import math
from pathlib import Path
import random

import arcade
from arcade.gui import (
    UIManager, UITextureButton, UIAnchorLayout, UIBoxLayout, UILabel, UISlider
)
from arcade.types import Color

from client.Bullet import Bullet
from client.Tank import Tank
from client.assets.effects.FireEffect import FireEffect

from SettingsWindow import toggle_fullscreen

# from client.Tree import Tree

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
    def __init__(self, window, client_or_server, is_client, color_assignments=None, spawn_assignments=None):
        super().__init__()
        self.window = window
        toggle_fullscreen(self.window)

        self.game_width = self.window.width
        self.game_height = self.window.height

        self.background = arcade.Sprite(":assets:images/forestBG.jpg")

        self.background.center_x = self.game_width // 2
        self.background.center_y = self.game_height // 2

        self.client_or_server = client_or_server
        self.is_client = is_client

        self.color_assignments = color_assignments or {}
        self.spawn_assignments = spawn_assignments or {}

        arcade.set_background_color(arcade.color.DARK_GRAY)

        self.spawn_positions = [
            (100, 100),  # Bottom-left corner
            (self.game_width - 100, 100),  # Bottom-right corner
            (100, self.game_height - 100),  # Top-left corner
            (self.game_width - 100, self.game_height - 100)  # Top-right corner
        ]

        # Tanks
        self.tanks = arcade.SpriteList()
        self.other_player_tanks = {}

        player_id = "host" if not is_client else self.client_or_server.player_name

        spawn_index = 0
        if is_client:
            # Clients get positions 1-3
            if self.client_or_server.client_id is not None:
                spawn_index = (self.client_or_server.client_id % 3) + 1
            # Fallback to random position if client_id not available
            else:
                spawn_index = random.randint(1, 3)

        # Host gets position 0 (bottom-left)
        spawn_position = self.spawn_positions[spawn_index]

        if not is_client:
            # Server/host uses its pre-assigned server_color
            if hasattr(self.client_or_server, 'server_color') and self.client_or_server.server_color:
                tank_color = self.client_or_server.server_color
                print(f"Server using server_color: {tank_color}")
            elif player_id in self.color_assignments:
                tank_color = self.color_assignments[player_id]
                print(f"Server using color_assignments: {tank_color}")
            else:
                tank_color = "red"  # Changed fallback from blue to red for server
                print(f"Server using fallback color: {tank_color}")
        else:
            # Client uses assigned_color or color_assignments
            if hasattr(self.client_or_server, 'assigned_color') and self.client_or_server.assigned_color:
                tank_color = self.client_or_server.assigned_color
                print(f"Client using assigned_color: {tank_color}")
            elif player_id in self.color_assignments:
                tank_color = self.color_assignments[player_id]
                print(f"Client using color_assignments: {tank_color}")
            else:
                # Final fallback for clients
                tank_color = "blue"
                print(f"Client using fallback color: {tank_color}")

        self.player_tank = Tank(tank_color=tank_color, player_id=player_id)
        self.player_tank.center_x = spawn_position[0]
        self.player_tank.center_y = spawn_position[1]
        self.player_tank.is_rotating = True

        self.tanks.append(self.player_tank)

        self.initial_position_sent = False

        arcade.schedule(self.send_tank_update, 1 / 64)
        arcade.schedule(self.process_queued_tank_updates, 1 / 64)

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
            background_box.with_background(color=Color(0, 0, 0, 200))
            background_box.add(child=layout, anchor_x="center", anchor_y="center")

            self.popup_box = background_box
            self.manager.add(self.popup_box)

            self.popup_active = True

    def on_draw(self):
        self.clear()

        # Simple drawing without camera
        arcade.draw_sprite(self.background)

        # Draw game elements
        for tank in self.tanks:
            tank.bullet_list.draw()
            tank.effects_list.draw()

        self.tanks.draw()

        if self.show_hitboxes:
            for tank in self.tanks:
                tank.bullet_list.draw_hit_boxes(arcade.color.RED)
            self.tanks.draw_hit_boxes(arcade.color.GREEN)

        if self.game_over:
            arcade.draw_text("GAME OVER - TANK DESTROYED!",
                             self.game_width / 2, self.game_height / 2,
                             arcade.color.RED, 24, anchor_x="center")

        # Draw UI elements
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
            # Use actual window size for boundary checking
            tank.update(delta_time, self.game_width, self.game_height)

            hit_tank = tank.check_bullet_collisions([t for t in self.tanks if t != tank])
            if hit_tank and hit_tank == self.player_tank and hit_tank.destroyed:
                self.game_over = True

    def on_back_click(self, event):

        arcade.unschedule(self.send_tank_update)
        arcade.unschedule(self.process_queued_tank_updates)

        self.manager.disable()
        from MainMenu import Mainview
        toggle_fullscreen(self.window)
        self.manager.clear()
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
            "tank_color": self.player_tank.tank_color,
        }

        if not self.initial_position_sent:
            tank_data["initial_spawn"] = True
            self.initial_position_sent = True

        if hasattr(self.player_tank, 'new_bullets') and self.player_tank.new_bullets:
            bullet_data = []
            for bullet in self.player_tank.new_bullets:
                bullet_data.append({
                    "x": bullet.center_x,
                    "y": bullet.center_y,
                    "angle": bullet.angle,
                    "speed": bullet.speed
                })
            tank_data["new_bullets"] = bullet_data
            self.player_tank.new_bullets = []

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

            if data.get("initial_spawn", False):
                new_tank.center_x = data.get("x")
                new_tank.center_y = data.get("y")
            else:
                # For non-initial packets for new tanks, use a corner position
                # to avoid spawning at the center
                spawn_index = len(self.other_player_tanks) + 1
                if spawn_index >= len(self.spawn_positions):
                    spawn_index = random.randrange(len(self.spawn_positions))
                new_tank.center_x = self.spawn_positions[spawn_index][0]
                new_tank.center_y = self.spawn_positions[spawn_index][1]

            self.other_player_tanks[player_id] = new_tank
            self.tanks.append(new_tank)

        # Update tank state
        tank = self.other_player_tanks[player_id]
        tank.center_x = data.get("x", tank.center_x)
        tank.center_y = data.get("y", tank.center_y)
        tank.angle = data.get("angle", tank.angle)
        tank.is_rotating = data.get("is_rotating", tank.is_rotating)
        tank.is_moving = data.get("is_moving", tank.is_moving)

        if "new_bullets" in data:
            for bullet_info in data["new_bullets"]:
                # Create bullet at the specified position
                bullet = Bullet(
                    ":assets:images/bullet.png",  # Use the appropriate bullet image
                    0.55,
                    bullet_info["x"],
                    bullet_info["y"],
                    bullet_info["angle"],
                    tank  # Associate bullet with this tank
                )

                # Set bullet speed and update direction
                bullet.speed = bullet_info.get("speed", 800)
                bullet.direction_radians = math.radians(bullet.angle)

                # Add to tank's bullet list, so it will be updated and drawn
                tank.bullet_list.append(bullet)

                # Add fire effect for visual feedback
                angle_rad = math.radians(bullet.angle)
                fire_effect = FireEffect(":assets:images/fire.png", 0.5,
                                         bullet.center_x, bullet.center_y, bullet.angle)
                tank.effects_list.append(fire_effect)
