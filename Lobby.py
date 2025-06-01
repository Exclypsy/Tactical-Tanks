import arcade
from arcade.gui import (
    UIView,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UITextureButton,
)
from arcade.types import Color
from pathlib import Path
from GameButton import GameButton
import json
from LobbyPlayer import TankButton

project_root = Path(__file__).resolve().parent
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
    print("️Nastal problém pri načítaní settings.json – používa sa prázdne nastavenie.")
    settings = {}

# Default player name if not set
player_name = settings.get("player_name", "Player")

class LobbyView(UIView):
    def __init__(self, window, client_or_server, is_client):
        super().__init__()
        self.window = window
        self.client_or_server = client_or_server
        self.is_client = is_client
        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        self.show_loading = False

        # Remove all old polling variables - use only real-time updates
        self.temp_player_list = []

        # Server IP display
        server_ip = client_or_server.get_server_ip()
        server_ip_label = UILabel(text="Server IP: " + server_ip[0] + ":" + str(server_ip[1]),
                                  font_size=20, text_color=arcade.color.WHITE)
        anchor = UIAnchorLayout()
        anchor.add(child=server_ip_label, anchor_x="left", anchor_y="top", align_x=10, align_y=-10)
        self.ui.add(anchor)

        # Create layout for players
        self.player_layout = UIBoxLayout(vertical=False, space_between=20)
        self.player_container = UIAnchorLayout(children=[self.player_layout], anchor_x="center", anchor_y="center")
        self.ui.add(self.player_container)

        # Exit button
        exit_button = UITextureButton(
            texture=TEX_EXIT_BUTTON,
            texture_hovered=TEX_EXIT_BUTTON,
            texture_pressed=TEX_EXIT_BUTTON,
            width=40, height=40
        )
        exit_button.on_click = self.on_back_click
        anchor = UIAnchorLayout()
        anchor.add(child=exit_button, anchor_x="right", anchor_y="top", align_x=-10, align_y=-10)
        self.ui.add(anchor)

        # INSTANT LOADING: Load initial players immediately
        self.load_initial_players()

        # Set up real-time updates for server
        if not self.is_client:
            self.client_or_server.lobby_update_callback = self.force_player_list_update

            # Add play button for server
            play_button = GameButton(text="PLAY")
            play_button.on_click = self.on_play_click
            anchor = UIAnchorLayout()
            anchor.add(child=play_button, anchor_x="center", anchor_y="bottom", align_y=30)
            self.ui.add(anchor)

    def load_initial_players(self):
        """Load initial player list with retry mechanism"""
        try:
            if self.is_client:
                # For clients, try multiple approaches
                max_attempts = 3

                for attempt in range(max_attempts):
                    print(f"Attempt {attempt + 1} to load player list...")

                    # First check cached data
                    initial_players = self.client_or_server.get_latest_player_list()
                    if initial_players:
                        print(f"Using cached player list: {[p[1] for p in initial_players]}")
                        self.temp_player_list = initial_players
                        self._update_player_buttons()
                        return

                    # If no cached data, request fallback
                    if attempt < max_attempts - 1:  # Don't wait on last attempt
                        print("No cached data, requesting fallback...")
                        network_players = self.client_or_server.get_players_list()
                        if network_players:
                            print(f"Fallback successful: {[p[1] for p in network_players]}")
                            self.temp_player_list = network_players
                            self._update_player_buttons()
                            return

                        # Wait a bit before retry
                        import time
                        time.sleep(0.3)

                # If all attempts failed, start with empty list and wait for real-time updates
                print("All loading attempts failed - waiting for real-time updates")
                self.temp_player_list = []
                self._update_player_buttons()
            else:
                # For server, get current list directly
                network_players = self.client_or_server.get_players_list() or []
                print(f"Server player list: {[p[1] for p in network_players]}")
                self.temp_player_list = network_players
                self._update_player_buttons()

            print("Initial player list loading complete")
        except Exception as e:
            print(f"Error loading initial players: {e}")
            import traceback
            traceback.print_exc()

    def on_instant_player_update(self):
        """Handle instant player list updates from server"""
        try:
            # Get the latest player list from client
            updated_player_list = self.client_or_server.get_latest_player_list()
            print(f"Processing instant update: {[p[1] for p in updated_player_list]}")

            # Convert back to tuples if they're lists (from JSON)
            processed_list = []
            for player_data in updated_player_list:
                if isinstance(player_data, list) and len(player_data) == 2:
                    addr_data, display_name = player_data
                    # Convert addr back to tuple if it's a list
                    if isinstance(addr_data, list) and len(addr_data) == 2:
                        addr_tuple = tuple(addr_data)
                    else:
                        addr_tuple = addr_data
                    processed_list.append((addr_tuple, display_name))
                else:
                    processed_list.append(player_data)

            # Update display immediately
            self.temp_player_list = processed_list
            self._update_player_buttons()

            print("Player list updated instantly!")

        except Exception as e:
            print(f"Error processing instant player update: {e}")
            import traceback
            traceback.print_exc()

    def extract_color_from_player_info(self, player_text):
        """Extract color and clean name from player info string"""
        # Handle different formats
        if "," in player_text:
            # Format: "IP:PORT,PlayerName (color)" or "IP:PORT,PlayerName (color) (host)"
            _, name_part = player_text.split(",", 1)
        else:
            # Format: "PlayerName (color)" or "PlayerName (color) (host)"
            name_part = player_text

        # Extract color using regex - look for (color) pattern
        import re
        color_match = re.search(r'\((\w+)\)(?:\s*\([^)]*\))?', name_part)
        if color_match:
            color = color_match.group(1).lower()
            # Remove all parenthetical parts to get clean name
            clean_name = re.sub(r'\s*\([^)]*\)', '', name_part).strip()
            # Check if it's a host
            is_host = "(host)" in name_part.lower() or "(Host)" in name_part
            return clean_name, color, is_host
        else:
            # Fallback - remove any parentheses and use default color
            clean_name = re.sub(r'\s*\([^)]*\)', '', name_part).strip()
            return clean_name, "blue", False


    def _update_player_buttons(self):
        """Update player buttons instantly"""
        # Clear existing buttons
        self.player_layout.clear()

        print(f"Updating buttons for {len(self.temp_player_list)} players")

        # Add buttons for each player instantly
        for player in self.temp_player_list:
            player_text = player[1]
            clean_name, color, is_host = self.extract_color_from_player_info(player_text)

            # Handle host display
            if is_host:
                display_name = f"{clean_name}\n(HOST)"
            else:
                display_name = clean_name

            print(f"Creating button for: {display_name} with color: {color}")

            # Create tank button with appropriate color
            tank_button = TankButton(
                name_text=display_name,
                color=color,
                button_width=180,
                button_height=180,
                font_size=16
            )

            self.player_layout.add(tank_button)


    def on_back_click(self, event):
        """Handle back button click with proper cleanup and disconnect"""
        print("Back button clicked in lobby")

        # Disconnect based on role
        if self.is_client:
            print("Client leaving lobby...")
            self.client_or_server.disconnect()
        else:
            print("Server shutting down from lobby...")
            self.client_or_server.send_server_disconnect(notify_clients=True)

        # Clear reference
        self.client_or_server = None

        # Return to main menu
        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

    def force_player_list_update(self):
        """Force immediate player list update (called from server)"""
        try:
            network_players = self.client_or_server.get_players_list() or []
            self.temp_player_list = network_players
            self._update_player_buttons()
            print("Player list force updated")
        except Exception as e:
            print(f"Error in forced player list update: {e}")

    def on_draw_before_ui(self):
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )

    def on_draw_after_ui(self):
        if self.show_loading:
            arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, Color(0, 0, 0, 170))

    def on_play_click(self, event):
        if not self.is_client:
            self.show_loading = True

            self.client_or_server.broadcast_selected_map()

            # Send with acknowledgment requirement
            self.client_or_server.send_command("game_start", require_ack=True)


            # Schedule the server to transition to game view after a short delay
            arcade.schedule_once(self.start_game_for_server, 0.5)

    def start_game_for_server(self, delta_time):
        if not self.is_client:
            self.show_loading = False

        from client.game import GameView
        self.window.show_view(GameView(self.window, self.client_or_server, False))

