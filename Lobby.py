import time

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
import re
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
        self.retry_timer = 0
        self.window = window
        self.client_or_server = client_or_server
        self.is_client = is_client
        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        self.show_loading = False

        self.temp_player_list = []
        self.last_known_server_name = "Server"

        self.update_counter = 0
        self.player_timeout_counts = {}
        self.max_timeout_count = 4

        # Server IP display
        server_ip = client_or_server.get_server_ip()
        server_ip = UILabel(text="Server IP: " + server_ip[0]+":"+str(server_ip[1]), font_size=20,
                            text_color=arcade.color.WHITE)
        anchor = UIAnchorLayout()
        anchor.add(child=server_ip, anchor_x="left", anchor_y="top", align_x=10, align_y=-10)
        self.ui.add(anchor)

        # Create layout for players - store as instance variable
        self.player_layout = UIBoxLayout(vertical=False, space_between=20)
        self.player_container = UIAnchorLayout(children=[self.player_layout], anchor_x="center", anchor_y="center")
        self.ui.add(self.player_container)

        # Exit button in top-right corner
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

        # Initial player list update
        self.update_player_list()
        # Schedule periodic updates
        arcade.schedule(self.update_player_list, 1.0)

        if not self.is_client:
            play_button = GameButton(text="PLAY")
            play_button.on_click = self.on_play_click
            anchor = UIAnchorLayout()
            anchor.add(child=play_button, anchor_x="center", anchor_y="bottom", align_y=30)
            self.ui.add(anchor)

        if self.is_client:
            # Request server info and wait a moment
            self.client_or_server.command_send_receive(b"get_server_name")
            # Give time for response
            time.sleep(0.1)
            self.host_name = getattr(self.client_or_server, 'server_name', "Server")
            self.host_color = getattr(self.client_or_server, 'server_color', "blue")
        else:
            self.host_name = getattr(self.client_or_server, 'player_name', player_name)
            self.host_color = getattr(self.client_or_server, 'server_color', "blue")

        print(f"Host name: {self.host_name}, Host color: {self.host_color}")
        self.add_server()

    def extract_color_from_player_info(self, player_text):
        """Extract color and clean name from player info string like 'PlayerName (color)' or 'PlayerName (color) (host)'"""
        # Handle different formats
        if "," in player_text:
            # Format: "IP:PORT,PlayerName (color)" or "IP:PORT,PlayerName (color) (host)"
            _, name_part = player_text.split(",", 1)
        else:
            # Format: "PlayerName (color)" or "PlayerName (color) (host)"
            name_part = player_text

        # Extract color using regex - look for (color) pattern
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

    def add_server(self):
        """Add server to the lobby with proper color"""
        server_color = getattr(self, 'host_color', 'blue')
        host_name = getattr(self, 'host_name', 'Server')

        print(f"Adding server: {host_name} ({server_color})")

        # Create tank button for server/host
        tank_button = TankButton(
            name_text=f"{host_name}\n(HOST)",
            color=server_color,
            button_width=180,
            button_height=180,
            font_size=16
        )
        self.player_layout.add(tank_button)

    def update_player_list(self, delta_time=None):
        """Update the player list with better error handling"""
        try:
            if self.client_or_server is None:
                arcade.unschedule(self.update_player_list)
                return

            self.update_counter += 1
            if self.update_counter % 2 != 0:
                return

            try:
                network_players = self.client_or_server.get_players_list() or []

                if not hasattr(self, 'player_timeout_counts'):
                    self.player_timeout_counts = {}
                    self.max_timeout_count = 4

                # Process the network players properly
                updated_player_list = []

                # Add all network players (including server if it's in the list)
                for player in network_players:
                    updated_player_list.append(player)
                    player_name = player[1]
                    self.player_timeout_counts[player_name] = 0

                # Handle timeout logic for missing players
                for player in self.temp_player_list:
                    player_name = player[1]
                    if any(p[1] == player_name for p in network_players):
                        continue  # Already added

                    timeout_count = self.player_timeout_counts.get(player_name, 0) + 1
                    self.player_timeout_counts[player_name] = timeout_count

                    if timeout_count < self.max_timeout_count:
                        updated_player_list.append(player)
                    else:
                        print(f"Removing player {player_name} after {self.max_timeout_count} timeouts")

                if self._has_player_list_changed(self.temp_player_list, updated_player_list):
                    self.temp_player_list = updated_player_list
                    self._update_player_buttons()

            except Exception as e:
                print(f"Error getting players: {e}")

        except Exception as e:
            print(f"Error updating player list: {e}")
    def _update_player_buttons(self):
        """Update player buttons using TankButton with correct colors"""
        # Clear existing buttons
        self.player_layout.clear()

        # Track if we've added the server
        server_added = False

        # Add buttons for each player
        for player in self.temp_player_list:
            player_text = player[1]
            clean_name, color, is_host = self.extract_color_from_player_info(player_text)

            # Handle host display
            if is_host:
                display_name = f"{clean_name}\n(HOST)"
                server_added = True
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

        # If server wasn't in the list, add it manually
        if not server_added and hasattr(self, 'host_name'):
            self.add_server()

    def _get_player_color_from_server(self, player_name):
        """Get player color from server assignments"""
        # Remove host indicators for matching
        clean_name = player_name.replace(" (host)", "").replace(" (Host)", "").strip()

        # For clients, check if we have server color info
        if self.is_client:
            if hasattr(self.client_or_server, 'server_color') and clean_name == getattr(self.client_or_server,'server_name', ''):
                return self.client_or_server.server_color

            if hasattr(self.client_or_server, 'color_assignments'):
                return self.client_or_server.color_assignments.get(clean_name, "blue")

        # For servers, get from server's player_colors
        if not self.is_client and hasattr(self.client_or_server, 'player_colors'):
            return self.client_or_server.player_colors.get(clean_name, "blue")

        # Default fallback
        return "blue"

    def _has_player_list_changed(self, old_list, new_list):
        """Helper to detect actual changes in the player list"""
        if len(old_list) != len(new_list):
            return True

        # Compare players by name to avoid flicker from changing IPs
        old_names = [p[1] for p in old_list]
        new_names = [p[1] for p in new_list]

        return set(old_names) != set(new_names)

    def _refresh_player_ui(self):
        """Update the UI with current player list"""
        # Clear existing player buttons
        self.player_layout.clear()

        # Add player buttons to layout using the temporary list
        for player in self.temp_player_list:
            player_text = f"{player[1]}"
            player_button = GameButton(text=player_text, width=200, height=50)
            self.player_layout.add(player_button)
        # self.add_server()

    def on_back_click(self, event):
        # Unschedule the update function to prevent errors after view change
        arcade.unschedule(self.update_player_list)

        # Disconnect from server
        if self.is_client:
            self.client_or_server.disconnect()
        else:
            self.client_or_server.shutdown()
        self.client_or_server = None

        from MainMenu import Mainview
        self.window.show_view(Mainview(self.window))

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

            arcade.unschedule(self.update_player_list)

            # Schedule the server to transition to game view after a short delay
            arcade.schedule_once(self.start_game_for_server, 0.5)

    def check_game_start(self, delta_time):
        """Check if game has started, resend command if needed"""
        if self.client_or_server is None:
            # Stop this scheduled function since client_or_server is no longer valid
            arcade.unschedule(self.check_game_start)
            return

        self.retry_timer += delta_time

        # If we've waited more than 5 seconds and game hasn't started
        if self.retry_timer > 5.0:
            print("Game start timeout, resending command")
            self.client_or_server.send_command("game_start", require_ack=True)
            self.retry_timer = 0

    def start_game_for_server(self, delta_time):
        if not self.is_client:
            self.show_loading = False

        # Unschedule all periodic functions
        arcade.unschedule(self.update_player_list)
        arcade.unschedule(self.check_game_start)

        from client.game import GameView
        self.window.show_view(GameView(self.window, self.client_or_server, False))

