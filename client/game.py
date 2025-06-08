import json
import math
import time
from pathlib import Path
import random
import arcade
from arcade import LBWH
from arcade.gui import (
    UIManager, UITextureButton, UIAnchorLayout, UIBoxLayout, UILabel, UISlider
)
from arcade.types import Color
from client.Bullet import Bullet
from client.Tank import Tank
from client.assets.effects.FireEffect import FireEffect
from non_player.StaticEntity import StaticEntity
from non_player.EntityManager import EntityManager
from client.assets.effects.EffectsManager import EffectsManager
from client.assets.effects.ExplosionEffect import ExplosionEffect
from client.assets.effects.OutlinedText import OutlinedText



# Resource paths
project_root = Path(__file__).resolve().parent.parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))
path = project_root / ".config" / "maps"
arcade.resources.add_resource_handle("maps", str(path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")

# Load settings
SETTINGS_FILE = project_root / ".config" / "settings.json"
settings = {}
try:
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
except json.JSONDecodeError:
    settings = {}


class MapBoundary:
    """Represents a map boundary for collision detection"""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center_x = x + width / 2
        self.center_y = y + height / 2

    def check_collision_with_point(self, x, y):
        """Check if a point collides with this boundary"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def check_collision_with_sprite(self, sprite):
        """Check if a sprite collides with this boundary"""
        return (sprite.center_x - sprite.width / 2 < self.x + self.width and
                sprite.center_x + sprite.width / 2 > self.x and
                sprite.center_y - sprite.height / 2 < self.y + self.height and
                sprite.center_y + sprite.height / 2 > self.y)


class GameView(arcade.View):
    def __init__(self, window, client_or_server, is_client, color_assignments=None, spawn_assignments=None):
        super().__init__()

        window.set_vsync(True)


        # Fixed game resolution - this defines the logical game world size
        self.GAME_WIDTH = 1920
        self.GAME_HEIGHT = 1080

        self.window = window
        self.client_or_server = client_or_server
        self.is_client = is_client
        self.color_assignments = color_assignments or {}
        self.spawn_assignments = spawn_assignments or {}


        # Create camera for scaling
        self.game_camera = arcade.camera.Camera2D()
        self.ui_camera = arcade.camera.Camera2D()

        # Map data
        self.current_map = client_or_server.current_map if is_client else client_or_server.picked_map
        self.map_data = None
        self.spawn_positions = []
        self.background = None

        # Map boundaries
        self.map_boundaries = []
        self.boundary_thickness = 20

        # Static entities
        self.entity_manager = EntityManager()
        self.static_entities = arcade.SpriteList()

        # Load the map first
        self.load_map(self.current_map)

        # Tanks
        self.tanks = arcade.SpriteList()
        self.other_player_tanks = {}
        self.player_tank = None

        # Scoreboard management
        self.scoreboard = {}
        self.death_order = []
        self.show_scoreboard = False

        # Initialize player tank with map spawn data
        self.setup_player_tank()

        # Schedule updates
        arcade.schedule(self.send_tank_update, 1 / 64)
        arcade.schedule(self.process_queued_tank_updates, 1 / 64)

        # UI setup
        self.manager = None
        self.setup_ui()

        # Debug and game state
        self.show_hitboxes = False
        self.game_over = False
        self.popup_active = False
        self.popup_box = None
        self.volume_slider = None
        self.initial_position_sent = False
        self.hitbox_line_thickness = 2

        self.last_resize_time = 0
        self.resize_delay = 0.05

        self.setup_cameras()

        self.effects_manager = EffectsManager()

        # Auto rematch functionality
        self.game_ended = False
        self.winner_name = None
        self.end_game_timer = 0
        self.rematch_delay = 5.0
        self.flash_timer = 0
        self.original_spawn_positions = {}  # Store original positions for restart

        self.game_start_time = 0
        self.winner_check_delay = 5.0  # 5 seconds delay before checking for winners
        self.winner_check_enabled = False

        self.start_game_timer()

    def start_game_timer(self):
        """Start the game timer for winner check delay"""
        self.game_start_time = 0
        self.winner_check_enabled = False
        print("Game started! Winner checking will begin in 5 seconds...")

    def setup_cameras(self):
        """Set up cameras using modern Arcade camera methods"""
        window_width = self.window.width
        window_height = self.window.height

        # Calculate scale maintaining aspect ratio
        scale_x = window_width / self.GAME_WIDTH
        scale_y = window_height / self.GAME_HEIGHT
        scale = min(scale_x, scale_y)

        # Create game camera
        self.game_camera = arcade.camera.Camera2D()

        # Set viewport dimensions
        self.game_camera.viewport_width = window_width
        self.game_camera.viewport_height = window_height

        # Position and zoom the camera
        self.game_camera.position = (self.GAME_WIDTH / 2, self.GAME_HEIGHT / 2)
        self.game_camera.zoom = scale

        # UI camera
        self.ui_camera = arcade.camera.Camera2D()
        self.ui_camera.viewport_width = window_width
        self.ui_camera.viewport_height = window_height
        self.ui_camera.position = (window_width / 2, window_height / 2)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.setup_cameras()

        # Update the last resize time
        self.last_resize_time = time.time()

        # Schedule a delayed camera setup check
        arcade.schedule(self._delayed_camera_setup, self.resize_delay)

    def _delayed_camera_setup(self, delta_time):
        """Check if enough time has passed since last resize, then setup cameras"""
        if time.time() - self.last_resize_time >= self.resize_delay:
            self.setup_cameras()
            arcade.unschedule(self._delayed_camera_setup)


    def load_map(self, map_name):
        """Load map data from JSON file and create game objects"""
        if not map_name:
            print("ERROR: No map name provided")
            self.setup_default_map()
            return

        try:
            map_file_path = project_root / ".config" / "maps" / f"{map_name}.json"
            if not map_file_path.exists():
                print(f"ERROR: Map file not found: {map_file_path}")
                self.setup_default_map()
                return

            with open(map_file_path, 'r') as file:
                self.map_data = json.load(file)

            print(f"Successfully loaded map: {map_name}")

            # Load background
            self.load_background()

            # Setup map boundaries
            self.setup_map_boundaries()

            # Load spawn positions
            self.load_spawn_positions()

            # Load static entities
            self.load_static_entities()

        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in map file {map_name}: {e}")
            self.setup_default_map()
        except Exception as e:
            print(f"ERROR: Failed to load map {map_name}: {e}")
            self.setup_default_map()

    def setup_default_map(self):
        """Setup default map if loading fails"""
        print("Setting up default map")
        self.map_data = {
            "map_info": {
                "name": "Default",
                "background": ":assets:images/forestBG.jpg"
            },
            "tank_spawns": [],
            "static_entities": []
        }

        # Default spawn positions using fixed game coordinates
        self.spawn_positions = [
            {"position": {"x": 100, "y": 100}, "rotation": 45},
            {"position": {"x": self.GAME_WIDTH - 100, "y": 100}, "rotation": 135},
            {"position": {"x": 100, "y": self.GAME_HEIGHT - 100}, "rotation": 315},
            {"position": {"x": self.GAME_WIDTH - 100, "y": self.GAME_HEIGHT - 100}, "rotation": 225}
        ]

        # Load default background
        self.load_background()
        self.setup_map_boundaries()

    def load_background(self):
        """Load and properly scale map background to fit fixed game resolution"""
        try:
            bg_path = self.map_data.get("map_info", {}).get("background", ":assets:images/forestBG.jpg")

            # Load the background texture
            background_texture = arcade.load_texture(bg_path)
            self.background = arcade.Sprite(background_texture)

            # Scale background to fit fixed game resolution
            texture_width = background_texture.width
            texture_height = background_texture.height

            # Calculate scale factors for both dimensions
            scale_x = self.GAME_WIDTH / texture_width
            scale_y = self.GAME_HEIGHT / texture_height

            # For stretching to fill exactly (may distort aspect ratio):
            self.background.scale_x = scale_x
            self.background.scale_y = scale_y

            # Center the background in game coordinates
            self.background.center_x = self.GAME_WIDTH // 2
            self.background.center_y = self.GAME_HEIGHT // 2

            print(
                f"Background scaled: {scale_x:.2f}x, {scale_y:.2f}y for game resolution {self.GAME_WIDTH}x{self.GAME_HEIGHT}")

        except Exception as e:
            print(f"ERROR: Failed to load background: {e}")
            # Fallback background creation
            self.background = arcade.Sprite(":assets:images/map_bg/forestBG.jpg")
            self.background.center_x = self.GAME_WIDTH // 2
            self.background.center_y = self.GAME_HEIGHT // 2

    def setup_map_boundaries(self):
        """Create invisible boundary walls around the fixed game resolution edges"""
        self.map_boundaries = [
            # Top boundary
            MapBoundary(-self.boundary_thickness, self.GAME_HEIGHT,
                        self.GAME_WIDTH + 2 * self.boundary_thickness, self.boundary_thickness),
            # Bottom boundary
            MapBoundary(-self.boundary_thickness, -self.boundary_thickness,
                        self.GAME_WIDTH + 2 * self.boundary_thickness, self.boundary_thickness),
            # Left boundary
            MapBoundary(-self.boundary_thickness, 0,
                        self.boundary_thickness, self.GAME_HEIGHT),
            # Right boundary
            MapBoundary(self.GAME_WIDTH, 0,
                        self.boundary_thickness, self.GAME_HEIGHT)
        ]

        print(f"Created {len(self.map_boundaries)} map boundaries for game resolution {self.GAME_WIDTH}x{self.GAME_HEIGHT}")

    def load_spawn_positions(self):
        """Load tank spawn positions from map data"""
        try:
            tank_spawns = self.map_data.get("tank_spawns", [])
            self.spawn_positions = []

            for spawn in tank_spawns:
                spawn_data = {
                    "position": spawn.get("position", {"x": 100, "y": 100}),
                    "rotation": spawn.get("rotation", 0)
                }
                self.spawn_positions.append(spawn_data)

            # Ensure we have at least 4 spawn positions using fixed game coordinates
            while len(self.spawn_positions) < 4:
                fallback_spawns = [
                    {"position": {"x": 100, "y": 100}, "rotation": 45},
                    {"position": {"x": self.GAME_WIDTH - 100, "y": 100}, "rotation": 135},
                    {"position": {"x": 100, "y": self.GAME_HEIGHT - 100}, "rotation": 315},
                    {"position": {"x": self.GAME_WIDTH - 100, "y": self.GAME_HEIGHT - 100}, "rotation": 225}
                ]
                self.spawn_positions.append(fallback_spawns[len(self.spawn_positions)])

            print(f"Loaded {len(self.spawn_positions)} spawn positions")

        except Exception as e:
            print(f"ERROR: Failed to load spawn positions: {e}")
            self.setup_default_map()

    def load_static_entities(self):
        """Load static entities from map data"""
        try:
            static_entities_data = self.map_data.get("static_entities", [])
            for entity_data in static_entities_data:
                try:
                    # Extract entity parameters
                    entity_type = entity_data.get("type", "bush_small")
                    position = entity_data.get("position", {"x": 500, "y": 500})
                    rotation = entity_data.get("rotation", 0)
                    scale = entity_data.get("scale", 1.0)
                    hp = entity_data.get("hp", 1)

                    # Create static entity
                    entity = StaticEntity(
                        x_pos=position["x"],
                        y_pos=position["y"],
                        entity_type=entity_type,
                        hp=hp,
                        scale=scale,
                        rotation=rotation
                    )

                    # Add to both the entity manager and sprite list
                    self.entity_manager.add_entity(entity)
                    self.static_entities.append(entity)

                except Exception as entity_error:
                    print(f"ERROR: Failed to create entity: {entity_error}")
                    continue

            print(f"Loaded {len(self.static_entities)} static entities")

        except Exception as e:
            print(f"ERROR: Failed to load static entities: {e}")

    def check_tank_boundary_collision(self, tank, new_x, new_y):
        """Check if tank would collide with map boundaries at new position"""
        # Create a temporary position to test
        old_x, old_y = tank.center_x, tank.center_y
        tank.center_x, tank.center_y = new_x, new_y

        collision = False
        for boundary in self.map_boundaries:
            if boundary.check_collision_with_sprite(tank):
                collision = True
                break

        # Restore original position
        tank.center_x, tank.center_y = old_x, old_y
        return collision

    def check_bullet_boundary_collision(self, bullet):
        """Check if bullet collides with map boundaries"""
        for boundary in self.map_boundaries:
            if boundary.check_collision_with_sprite(bullet):
                return True
        return False

    def setup_player_tank(self):
        """Setup the player tank with proper spawn position and color"""
        if not self.is_client:
            # Host should use their actual name, not just "host"
            if hasattr(self.client_or_server, 'player_name') and self.client_or_server.player_name:
                player_id = self.client_or_server.player_name
            elif hasattr(self.client_or_server, 'server_name') and self.client_or_server.server_name:
                player_id = self.client_or_server.server_name
            else:
                player_id = "host"  # Fallback only if no name is available
        else:
            player_id = self.client_or_server.player_name
        spawn_index = 0

        if self.is_client:
            # Clients get positions 1-3
            if self.client_or_server.client_id is not None:
                spawn_index = (self.client_or_server.client_id % 3) + 1
            else:
                spawn_index = random.randint(1, 3)

        # Get spawn position from map data
        if spawn_index < len(self.spawn_positions):
            spawn_data = self.spawn_positions[spawn_index]
            spawn_position = (spawn_data["position"]["x"], spawn_data["position"]["y"])
            spawn_rotation = spawn_data["rotation"]
        else:
            # Fallback to default positions using fixed game coordinates
            default_positions = [
                (100, 100), (self.GAME_WIDTH - 100, 100),
                (100, self.GAME_HEIGHT - 100), (self.GAME_WIDTH - 100, self.GAME_HEIGHT - 100)
            ]
            spawn_position = default_positions[spawn_index % len(default_positions)]
            spawn_rotation = 0

        # Determine tank color
        if not self.is_client:
            # Server/host uses its pre-assigned server_color
            if hasattr(self.client_or_server, 'server_color') and self.client_or_server.server_color:
                tank_color = self.client_or_server.server_color
            elif player_id in self.color_assignments:
                tank_color = self.color_assignments[player_id]
            else:
                tank_color = "red"
        else:
            # Client uses assigned_color or color_assignments
            if hasattr(self.client_or_server, 'assigned_color') and self.client_or_server.assigned_color:
                tank_color = self.client_or_server.assigned_color
            elif player_id in self.color_assignments:
                tank_color = self.color_assignments[player_id]
            else:
                tank_color = "blue"

        # Create player tank
        self.player_tank = Tank(tank_color=tank_color, player_id=player_id)
        self.player_tank.center_x = spawn_position[0]
        self.player_tank.center_y = spawn_position[1]
        self.player_tank.angle = spawn_rotation
        self.player_tank.is_rotating = True
        self.tanks.append(self.player_tank)

        if player_id not in self.scoreboard:
            self.scoreboard[player_id] = 0
            print(f"Initialized scoreboard for player: {player_id}")

    def setup_ui(self):
        """Setup the user interface"""
        self.manager = UIManager()
        self.manager.enable()

        # Exit button
        exit_button = UITextureButton(
            texture=TEX_EXIT_BUTTON,
            texture_hovered=TEX_EXIT_BUTTON,
            texture_pressed=TEX_EXIT_BUTTON,
            width=60,
            height=60
        )

        exit_button.on_click = self.toggle_pause_menu

        anchor = UIAnchorLayout()
        anchor.add(child=exit_button, anchor_x="right", anchor_y="top", align_x=-10, align_y=-10)
        self.manager.add(anchor)

    def on_draw(self):
        arcade.set_background_color(arcade.color.DARK_GRAY)
        # Clear the screen
        self.clear()

        # Draw game content with game camera
        self.game_camera.use()

        # Draw background
        if self.background:
            arcade.draw_sprite(self.background)

        # Draw static entities
        self.static_entities.draw()

        # Draw game elements
        for tank in self.tanks:
            tank.bullet_list.draw()
            tank.effects_list.draw()
        self.tanks.draw()

        self.effects_manager.draw()

        # Draw debug information
        if self.show_hitboxes:
            for tank in self.tanks:
                tank.bullet_list.draw_hit_boxes(arcade.color.RED,self.hitbox_line_thickness)
            self.tanks.draw_hit_boxes(arcade.color.GREEN,self.hitbox_line_thickness)
            self.static_entities.draw_hit_boxes(arcade.color.BLUE,self.hitbox_line_thickness)

            for boundary in self.map_boundaries:
                arcade.draw_lrbt_rectangle_outline(
                    boundary.x, boundary.x + boundary.width,
                    boundary.y, boundary.y + boundary.height,
                    arcade.color.YELLOW, 2
                )

        # Switch to UI camera for UI elements
        self.ui_camera.use()

        if self.show_scoreboard:
            self.draw_scoreboard_overlay()

        # Draw UI elements
        self.manager.draw()

        if self.show_hitboxes:
            # Draw viewport bounds
            vp = self.game_camera.viewport
            arcade.draw_rect_outline(LBWH(vp[0] + vp[2] / 2, vp[1] + vp[3] / 2, vp[2], vp[3]), arcade.color.RED, 3)

    def on_update(self, delta_time):

        # Handle game end sequence
        if self.game_ended:
            self.end_game_timer += delta_time
            self.flash_timer += delta_time

            # Scoreboard timing logic
            if 0.3 <= self.end_game_timer < self.rematch_delay:
                self.show_scoreboard = True
            else:
                # Hide scoreboard before 1 second and after 5 seconds
                self.show_scoreboard = False


            # Auto restart after delay
            if self.end_game_timer >= self.rematch_delay:
                self.restart_game()
                return

            # Update game start timer and enable winner checking after delay
        if not self.winner_check_enabled and len(self.tanks) >= 2:
            self.game_start_time += delta_time
            if self.game_start_time >= self.winner_check_delay:
                self.winner_check_enabled = True
                print("Winner checking now enabled!")

            # Check for game end condition (only if enabled)
        self.check_game_end_condition()

        self.effects_manager.update(delta_time)

        all_bullets = arcade.SpriteList()

        # Update tanks with sliding collision
        for tank in self.tanks:
            all_bullets.extend(tank.bullet_list)

            # Store old position for collision checking
            old_x, old_y = tank.center_x, tank.center_y

            # Let tank update normally (including recoil) but skip regular movement
            tank.update(delta_time, self.GAME_WIDTH, self.GAME_HEIGHT, skip_movement=True)

            # Check if recoil caused collision and revert if needed
            if (self.check_tank_boundary_collision(tank, tank.center_x, tank.center_y) or
                    self.check_tank_static_entity_collision(tank, tank.center_x, tank.center_y)):
                # Recoil caused collision, revert to old position
                tank.center_x, tank.center_y = old_x, old_y

            # Store position after recoil (but before movement)
            post_recoil_x, post_recoil_y = tank.center_x, tank.center_y

            # Now handle movement collision detection separately
            if tank.is_moving and not tank.destroyed:
                if tank.destroyed and tank.player_id not in self.death_order:
                    self.record_tank_death(tank)

                # Calculate what the movement should have been
                angle_rad = math.radians(tank.angle)
                intended_delta_x = tank.speed * math.sin(angle_rad) * delta_time
                intended_delta_y = tank.speed * math.cos(angle_rad) * delta_time

                # Try X movement only
                new_x = post_recoil_x + intended_delta_x
                if not (self.check_tank_boundary_collision(tank, new_x, post_recoil_y) or
                        self.check_tank_static_entity_collision(tank, new_x, post_recoil_y)):
                    tank.center_x = new_x

                # Try Y movement only
                new_y = post_recoil_y + intended_delta_y
                if not (self.check_tank_boundary_collision(tank, tank.center_x, new_y) or
                        self.check_tank_static_entity_collision(tank, tank.center_x, new_y)):
                    tank.center_y = new_y

            # # Check bullet collisions with other tanks
            tank.check_bullet_collisions(
                [t for t in self.tanks if t != tank],
                self.effects_manager
            )

            # Check bullet collisions with boundaries
            for bullet in list(tank.bullet_list):
                if self.check_bullet_boundary_collision(bullet):
                    explosion = ExplosionEffect(bullet.center_x, bullet.center_y)
                    self.effects_manager.add_effect(explosion)
                    bullet.remove_from_sprite_lists()

        # Update entity manager with bullet collisions
        self.entity_manager.update(all_bullets, self.effects_manager)

        # Remove destroyed entities from our sprite list
        for entity in self.static_entities:
            if not entity.is_alive():
                entity.remove_from_sprite_lists()

    def toggle_pause_menu(self, event=None):
        if self.popup_active:
            self.manager.remove(self.popup_box)
            self.popup_active = False
        else:
            self.player_tank.is_moving = False

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

    def on_key_press(self, key, modifiers):
        if self.game_over:
            return

        if self.popup_active and key != arcade.key.ESCAPE:
            return

        if key == arcade.key.SPACE:
            self.player_tank.handle_key_press(key)
        elif key == arcade.key.H:
            self.show_hitboxes = not self.show_hitboxes
        elif key == arcade.key.ESCAPE:
            self.toggle_pause_menu()
        elif key == arcade.key.TAB:
            self.show_scoreboard = True

    def on_key_release(self, key, modifiers):
        if self.game_over:
            return

        if self.popup_active and key != arcade.key.ESCAPE:
            return

        if key == arcade.key.SPACE:
            self.player_tank.handle_key_release(key)
        elif key == arcade.key.TAB:
            self.show_scoreboard = False

    def on_back_click(self, event):
        """Handle exit from game with proper cleanup"""
        print("Exiting game...")

        # Unschedule specific functions instead of unschedule_all
        functions_to_unschedule = [
            self.send_tank_update,
            self.process_queued_tank_updates,
        ]

        # Add _delayed_camera_setup if it exists
        if hasattr(self, '_delayed_camera_setup'):
            functions_to_unschedule.append(self._delayed_camera_setup)

        for func in functions_to_unschedule:
            try:
                arcade.unschedule(func)
                print(f"Unscheduled {func.__name__}")
            except:
                pass  # Function might not be scheduled

        # Disable UI manager
        if hasattr(self, 'manager'):
            try:
                self.manager.disable()
                self.manager.clear()
                print("UI manager disabled and cleared")
            except:
                pass

        # Handle network cleanup
        if self.client_or_server:
            if self.is_client:
                print("Client disconnecting from game...")
                self.client_or_server.disconnect()
            else:
                print("Server shutting down from game...")
                self.client_or_server.send_server_disconnect(notify_clients=True)

            self.client_or_server = None

        # Return to main menu
        from MainMenu import Mainview
        from SettingsWindow import toggle_fullscreen, settings

        if settings.get("fullscreen", True):
            toggle_fullscreen(self.window)

        self.window.show_view(Mainview(self.window))
        print("Returned to main menu")

    def process_queued_tank_updates(self, delta_time=None):
        """Process any queued tank updates from the networking thread"""
        if not self.client_or_server:
            return

        updates_to_process = []
        if hasattr(self.client_or_server, 'pending_tank_updates'):
            with self.client_or_server.tank_updates_lock:
                updates_to_process = self.client_or_server.pending_tank_updates.copy()
                self.client_or_server.pending_tank_updates.clear()

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

        # Handle player disconnection
        if data.get("type") == "player_disconnected":
            print(f"Player {player_id} disconnected during game")
            if player_id in self.other_player_tanks:
                tank = self.other_player_tanks[player_id]
                tank.take_damage(100)  # Kill the tank
                tank.destroyed = True
                print(f"Marked tank {player_id} as dead due to disconnect")
            return

        # print(f"Processing tank update: {player_id} (our ID: {self.player_tank.player_id})")

        # Create or update the tank for this player
        if player_id not in self.other_player_tanks:
            print(f"Creating new tank for player: {player_id}")
            tank_color = data.get("tank_color", "blue")
            new_tank = Tank(tank_color=tank_color, player_id=player_id)

            if data.get("initial_spawn", False):
                new_tank.center_x = data.get("x")
                new_tank.center_y = data.get("y")
            else:
                # Use map spawn positions for new tanks
                spawn_index = len(self.other_player_tanks) + 1
                if spawn_index < len(self.spawn_positions):
                    spawn_data = self.spawn_positions[spawn_index]
                    new_tank.center_x = spawn_data["position"]["x"]
                    new_tank.center_y = spawn_data["position"]["y"]
                    new_tank.angle = spawn_data["rotation"]
                else:
                    # Fallback to random spawn
                    spawn_index = random.randrange(len(self.spawn_positions))
                    spawn_data = self.spawn_positions[spawn_index]
                    new_tank.center_x = spawn_data["position"]["x"]
                    new_tank.center_y = spawn_data["position"]["y"]
                    new_tank.angle = spawn_data["rotation"]

            self.other_player_tanks[player_id] = new_tank
            self.tanks.append(new_tank)

            if player_id not in self.scoreboard:
                self.scoreboard[player_id] = 0
                print(f"Initialized scoreboard for new player: {player_id}")

        # Update tank state
        tank = self.other_player_tanks[player_id]
        tank.center_x = data.get("x", tank.center_x)
        tank.center_y = data.get("y", tank.center_y)
        tank.angle = data.get("angle", tank.angle)
        tank.is_rotating = data.get("is_rotating", tank.is_rotating)
        tank.is_moving = data.get("is_moving", tank.is_moving)

        if "new_bullets" in data:
            for bullet_info in data["new_bullets"]:
                bullet = Bullet(
                    ":assets:images/bullet.png",
                    0.5,
                    bullet_info["x"],
                    bullet_info["y"],
                    bullet_info["angle"],
                    tank
                )
                bullet.speed = bullet_info.get("speed", 800)
                bullet.direction_radians = math.radians(bullet.angle)
                tank.bullet_list.append(bullet)

                # Add fire effect
                fire_effect = FireEffect(":assets:images/fire.png", 0.5,
                                         bullet.center_x, bullet.center_y, bullet.angle)
                tank.effects_list.append(fire_effect)

    def check_game_end_condition(self):
        """Check if only one player is alive and handle game end"""
        # Don't check for winners if game already ended
        if self.game_ended:
            return

        # Don't check for winners until delay has passed
        if not self.winner_check_enabled:
            return

        alive_tanks = []
        for tank in self.tanks:
            if not tank.destroyed:
                alive_tanks.append(tank)

        # Game ends when only one tank is alive (or no tanks alive)
        if len(alive_tanks) <= 1:
            self.game_ended = True
            self.end_game_timer = 0

            # Calculate and update scoreboard
            self.calculate_and_update_scoreboard()


            if len(alive_tanks) == 1:
                winner_tank = alive_tanks[0]
                # Stop the winner's rotation
                winner_tank.is_rotating = False
                winner_tank.is_moving = False

                # Get winner name
                self.winner_name = winner_tank.player_id
                print(f"Game ended! Winner: {self.winner_name}")

                # If server, broadcast map selection AND load the new map
                if not self.is_client:
                    self.client_or_server.broadcast_selected_map()
                    self.current_map = self.client_or_server.picked_map
                else:
                    self.current_map = self.client_or_server.current_map
            else:
                # No survivors (draw)
                self.winner_name = "Nobody"
                print("Game ended in a draw!")

    def restart_game(self):
        print("Restarting game...")

        # Reset game state
        self.game_ended = False
        self.winner_name = None
        self.end_game_timer = 0
        self.flash_timer = 0
        self.game_start_time = 0
        self.winner_check_enabled = False
        self.show_scoreboard = False

        # Reset death tracking
        self.death_order = []

        # Clear only game objects, keep map data
        self.clear_game_objects()

        self.load_map(self.current_map)

        # Recreate player tank with existing spawn data
        self.setup_player_tank()

        # Reset multiplayer state
        self.initial_position_sent = False

        # Reset effects
        self.effects_manager = EffectsManager()

        # Start game timer
        self.start_game_timer()

        print("Game restarted successfully!")

    def clear_game_objects(self):
        print("Clearing game objects...")

        # Clear tanks and their components
        for tank in self.tanks:
            tank.bullet_list.clear()
            tank.effects_list.clear()
            if hasattr(tank, 'new_bullets'):
                tank.new_bullets.clear()
            tank.remove_from_sprite_lists()

        self.tanks.clear()
        self.other_player_tanks.clear()

        # Clear static entities
        for entity in self.static_entities:
            entity.remove_from_sprite_lists()
        self.static_entities.clear()

        # Reset entity manager
        self.entity_manager = EntityManager()


        # Clear pending network updates
        if hasattr(self.client_or_server, 'pending_tank_updates'):
            with self.client_or_server.tank_updates_lock:
                self.client_or_server.pending_tank_updates.clear()

        print("Game objects cleared successfully")

    def check_tank_static_entity_collision(self, tank, new_x, new_y):
        """Check if tank would collide with static entities at new position"""
        # Store original position
        old_x, old_y = tank.center_x, tank.center_y

        # Set temporary position
        tank.center_x, tank.center_y = new_x, new_y

        # Check collision with static entities using Arcade 3.0.1 feature
        collision_list = arcade.check_for_collision_with_list(tank, self.static_entities)

        # Restore original position
        tank.center_x, tank.center_y = old_x, old_y

        return len(collision_list) > 0

    def load_map_and_setup(self, map_name):
        """Client method: load map and setup after server selection"""
        print(f"Client loading and setting up map: {map_name}")

        # Set the game view's current_map to the new map
        self.current_map = map_name

        # Clear existing game objects
        self.clear_game_objects()

        # Then load the new map
        self.load_map(self.current_map)
        self.setup_player_tank()

        print("Client setup complete")

    def record_tank_death(self, tank):
        """Record when a tank dies for scoreboard purposes"""
        if tank.player_id not in self.death_order and tank.destroyed:
            self.death_order.append(tank.player_id)
            print(f"Tank {tank.player_id} died. Death order position: {len(self.death_order)}")

    def calculate_and_update_scoreboard(self):
        """Calculate scores based on survival order and update scoreboard"""
        # Initialize scoreboard entries for all players
        for tank in self.tanks:
            if tank.player_id not in self.scoreboard:
                self.scoreboard[tank.player_id] = 0

        # Find alive tanks (winners)
        alive_tanks = [tank for tank in self.tanks if not tank.destroyed]

        # Award points based on survival
        total_players = len(self.tanks)

        if len(alive_tanks) == 1:
            # One winner
            winner = alive_tanks[0]
            self.scoreboard[winner.player_id] += 3
            print(f"{winner.player_id} gets 3 points for winning!")

            # Award points to last survivors based on death order (reverse order)
            if len(self.death_order) >= 1:
                # Last to die before winner gets 2 points
                second_place = self.death_order[-1]
                self.scoreboard[second_place] += 2
                print(f"{second_place} gets 2 points for 2nd place!")

            if len(self.death_order) >= 2:
                # Second to last to die gets 1 point
                third_place = self.death_order[-2]
                self.scoreboard[third_place] += 1
                print(f"{third_place} gets 1 point for 3rd place!")

        elif len(alive_tanks) == 0:
            # All died - award points to last 3 survivors
            if len(self.death_order) >= 1:
                last_survivor = self.death_order[-1]
                self.scoreboard[last_survivor] += 3
                print(f"{last_survivor} gets 3 points for being last survivor!")

            if len(self.death_order) >= 2:
                second_last = self.death_order[-2]
                self.scoreboard[second_last] += 2
                print(f"{second_last} gets 2 points for 2nd place!")

            if len(self.death_order) >= 3:
                third_last = self.death_order[-3]
                self.scoreboard[third_last] += 1
                print(f"{third_last} gets 1 point for 3rd place!")

    def draw_scoreboard_overlay(self):
        """Draw the scoreboard overlay with darkened background"""
        # Draw darkened background
        arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, Color(0, 0, 0, 170))

        # Get sorted scoreboard data
        sorted_scores = sorted(self.scoreboard.items(), key=lambda x: x[1], reverse=True)

        if not sorted_scores:
            return

        # Calculate layout dimensions
        title_y = self.window.height // 2 + 150
        entry_height = 70
        start_y = title_y - 100

        # Draw title
        title_text = OutlinedText(
            "SCOREBOARD",
            self.window.width // 2, title_y,
            text_color=arcade.color.WHITE,
            outline_color=arcade.color.BLACK,
            font_size=48,
            stroke_width=8,
            anchor_x="center",
            anchor_y="center"
        )
        title_text.draw()

        # Calculate positioning for entries
        max_name_width = 0
        score_width = 60  # Approximate width for scores

        # First pass: calculate maximum name width for alignment
        for player_id, score in sorted_scores:
            name_width = len(player_id) * 14  # Approximate character width at font size 24
            max_name_width = max(max_name_width, name_width)

        # Entry layout calculations
        color_rect_width = 40
        name_start_x = self.window.width // 2 - 250
        color_rect_x = name_start_x - color_rect_width - 10
        score_end_x = self.window.width // 2 + 250
        dots_start_x = name_start_x + max_name_width + 20
        dots_end_x = score_end_x - score_width - 10

        # Draw each player entry
        for i, (player_id, score) in enumerate(sorted_scores):
            y_pos = start_y - (i * entry_height)

            # Get tank color for this player
            tank_color = self.get_player_tank_color(player_id)
            color_rgb = self.get_color_rgb(tank_color)

            # Draw tank color indicator (rounded rectangle)
            arcade.draw_lbwh_rectangle_filled(
                color_rect_x, y_pos - 15, color_rect_width, 30, color_rgb
            )

            # Draw black border around color indicator
            arcade.draw_lbwh_rectangle_outline(
                color_rect_x, y_pos - 15, color_rect_width, 30, arcade.color.BLACK, 2
            )

            # Draw player name with outline
            name_text = OutlinedText(
                player_id,
                name_start_x, y_pos,
                text_color=arcade.color.WHITE,
                outline_color=arcade.color.BLACK,
                font_size=24,
                stroke_width=3,
                anchor_x="left",
                anchor_y="center"
            )
            name_text.draw()

            # Draw score
            score_text = f"{score}"
            arcade.Text(
                score_text,
                score_end_x, y_pos,
                arcade.color.WHITE,
                font_size=24,
                anchor_x="right",
                anchor_y="center",
                font_name="ARCO"
            ).draw()

            # Draw dots between name and score
            self.draw_connecting_dots(dots_start_x, y_pos, dots_end_x)

    def get_player_tank_color(self, player_id):
        """Get the tank color for a specific player"""
        # Check current tanks first
        for tank in self.tanks:
            if tank.player_id == player_id:
                return tank.tank_color

        # Fallback to color assignments
        if player_id in self.color_assignments:
            return self.color_assignments[player_id]

        # Default fallback
        return "blue"

    def get_color_rgb(self, color_name):
        """Convert color name to RGB tuple"""
        color_map = {
            "blue": arcade.color.DODGER_BLUE,
            "red": arcade.color.RED,
            "green": arcade.color.LIME_GREEN,
            "yellow": arcade.color.YELLOW
        }
        return color_map.get(color_name.lower(), arcade.color.DODGER_BLUE)

    def draw_connecting_dots(self, start_x, y, end_x):
        """Draw connecting dots between player name and score with variable spacing"""
        available_width = end_x - start_x

        if available_width <= 0:
            return

        # Calculate optimal dot spacing
        dot_diameter = 3
        min_spacing = 8
        ideal_spacing = 12

        # Try ideal spacing first
        num_dots = int(available_width // ideal_spacing)

        if num_dots > 0:
            # Adjust spacing to distribute dots evenly
            actual_spacing = available_width / num_dots

            for i in range(num_dots):
                dot_x = start_x + (i * actual_spacing) + (actual_spacing / 2)
                arcade.draw_circle_filled(dot_x, y, dot_diameter // 2, arcade.color.GRAY)
