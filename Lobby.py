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

    def update_player_list(self, delta_time=None):
        """Update the player list display to reflect current connected players"""
        try:
            # Check if client_or_server is still valid
            if self.client_or_server is None:
                arcade.unschedule(self.update_player_list)
                return

            # Try to get current players without immediately updating the UI
            try:
                new_players = self.client_or_server.get_players_list()

                # Check if server is already in the list
                server_ip = self.client_or_server.get_server_ip()
                server_found = False

                for player in new_players:
                    # Check if this player entry matches the server IP
                    if isinstance(player[0], tuple) and player[0][0] == server_ip[0] and player[0][1] == server_ip[1]:
                        server_found = True
                        # Update last known server name if we find it in the list
                        self.last_known_server_name = player[1].replace(" (Host)", "")
                        break

                # Only add server player if not already in list
                if not server_found:
                    if self.is_client:
                        try:
                            server_name = str(self.client_or_server.command_send_receive(b"get_server_name"))
                            server_data = json.loads(server_name)
                            if "server_name" in server_data:
                                self.last_known_server_name = server_data["server_name"]
                                print(f"Lobby -> 127: Updated server name: {self.last_known_server_name}")
                        except Exception as e:
                            print(f"Error getting server name: {e}")
                            # Keep using the last known server name - don't reset it
                    else:
                        if self.client_or_server.player_name:
                            self.last_known_server_name = self.client_or_server.player_name
                            print(f"Lobby -> 130: Using local server name: {self.last_known_server_name}")

                    # Always use the cached server name to prevent UI flickering
                    new_players.append((server_ip, self.last_known_server_name + " (Host)"))

                # Only update temp list if we successfully got new data and it's not empty
                if new_players:
                    self.temp_player_list = new_players
                    print(f"Lobby -> Updated temporary player list: {self.temp_player_list}")

            except Exception as e:
                print(f"Error getting players: {e}")
                print(f"Keeping existing player list for UI consistency")
                # Don't update temp_player_list - keep using the existing one

            # Clear existing player buttons
            self.player_layout.clear()

            # Add player buttons to layout using the temporary list for consistency
            if self.temp_player_list:
                print(f"Lobby -> Displaying player list: {self.temp_player_list}")
                for i, player in enumerate(self.temp_player_list):
                    print(f"Lobby -> 113: {i, player}")
                    player_text = f"{player[1]}"
                    player_button = GameButton(text=player_text, width=200, height=50)
                    self.player_layout.add(player_button)
            else:
                # If temp list is still empty, show at least the server
                if self.is_client:
                    player_text = f"{self.last_known_server_name} (Host)"
                else:
                    player_text = f"{self.client_or_server.player_name or 'Server'} (Host)"
                player_button = GameButton(text=player_text, width=200, height=50)
                self.player_layout.add(player_button)

        except Exception as e:
            print(f"Error updating player list: {e}")

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

