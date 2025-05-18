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
            self.client_or_server.command_send_receive(b"get_server_name")
            self.host_name = getattr(self.client_or_server, 'server_name', "Server")
        else:
            self.host_name = getattr(self.client_or_server, 'player_name', player_name)
        print(f"Host name: {self.host_name}")
        self.add_server()

        self.update_counter = 0


    def add_server(self):
        if self.host_name is None:
            if self.is_client:
                self.client_or_server.command_send_receive(b"get_server_name")
                self.host_name = getattr(self.client_or_server, 'server_name', "Server")
            else:
                self.host_name = getattr(self.client_or_server, 'player_name', player_name)
            print(f"Host name: {self.host_name}")

        player_button = GameButton(text=str(self.host_name)+" (host)", width=200, height=50)
        self.player_layout.add(player_button)

    def update_player_list(self, delta_time=None):
        """Update the player list with 3-timeout threshold to reduce flickering"""
        try:
            # Check if client_or_server is still valid
            if self.client_or_server is None:
                arcade.unschedule(self.update_player_list)
                return

            # Throttle updates to reduce flickering
            self.update_counter += 1
            if self.update_counter % 2 != 0:  # Only update every other frame
                return

            try:
                # Get current network players
                network_players = self.client_or_server.get_players_list() or []

                # Initialize timeout tracking if needed
                if not hasattr(self, 'player_timeout_counts'):
                    self.player_timeout_counts = {}
                    self.max_timeout_count = 3  # Require 3 timeouts before removing a player

                # Create dict of players from network
                network_player_dict = {player[1]: player for player in network_players}

                # Start with empty updated list
                updated_player_list = []

                # First ensure host is present
                host_name = self.host_name if hasattr(self, 'host_name') else "Server"
                host_text = f"{host_name} (Host)"
                server_ip = self.client_or_server.get_server_ip()
                host_entry = (server_ip, host_text)
                updated_player_list.append(host_entry)

                # Process all network players first - they're definitely active
                for player_name, player in network_player_dict.items():
                    # Skip if this is a host entry
                    if "(Host)" in player_name:
                        continue

                    # Add player from network and reset timeout
                    updated_player_list.append(player)
                    self.player_timeout_counts[player_name] = 0

                # Now check for players in current display but not in network
                for player in self.temp_player_list:
                    player_name = player[1]

                    # Skip host or players already added from network
                    if "(Host)" in player_name or player_name in network_player_dict:
                        continue

                    # Player from UI not in network - apply timeout logic
                    timeout_count = self.player_timeout_counts.get(player_name, 0) + 1
                    self.player_timeout_counts[player_name] = timeout_count

                    # Keep player if below max timeout
                    if timeout_count < self.max_timeout_count:
                        updated_player_list.append(player)
                    else:
                        print(f"Removing player {player_name} after {self.max_timeout_count} timeouts")

                # Update UI if needed
                if self._has_player_list_changed(self.temp_player_list, updated_player_list):
                    self.temp_player_list = updated_player_list
                    self._update_player_buttons()

            except Exception as e:
                print(f"Error getting players: {e}")
        except Exception as e:
            print(f"Error updating player list: {e}")

    def _update_player_buttons(self):
        """Smart update of player buttons to minimize flickering"""
        # Get existing buttons and their names
        existing_buttons = {}
        for i, child in enumerate(self.player_layout.children):
            if isinstance(child, GameButton):
                existing_buttons[child.text] = (child, i)

        # Create a list of button operations to perform
        buttons_to_add = []

        # Figure out which buttons to keep and which to add
        for player in self.temp_player_list:
            player_text = player[1]
            if player_text in existing_buttons:
                # Button already exists, keep track of it
                existing_buttons[player_text] = (existing_buttons[player_text][0], -1)  # Mark as used
            else:
                # Need to create a new button
                buttons_to_add.append(player_text)

        # Remove unused buttons (ones still with positive indices)
        buttons_to_remove = []
        for text, (button, idx) in existing_buttons.items():
            if idx >= 0:
                buttons_to_remove.append(button)

        # Actually remove the buttons
        for button in buttons_to_remove:
            self.player_layout.remove(button)

        # Add new buttons
        for text in buttons_to_add:
            new_button = GameButton(text=text, width=200, height=50)
            self.player_layout.add(new_button)

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

