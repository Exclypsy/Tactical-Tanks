import arcade
from arcade.gui import (
    UIView,
    UIAnchorLayout,
    UIBoxLayout,
    UILabel,
    UITextureButton,
)
from pathlib import Path
from GameButton import GameButton

project_root = Path(__file__).resolve().parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

TEX_EXIT_BUTTON = arcade.load_texture(":assets:images/exit.png")


class LobbyView(UIView):
    def __init__(self, window, client_or_server, is_client):
        super().__init__()
        self.window = window
        self.client_or_server = client_or_server
        self.is_client = is_client
        self.background_color = arcade.color.DARK_BLUE
        self.background = arcade.load_texture(":assets:images/background.png")

        # Server IP display
        server_ip = UILabel(text="Server IP: " + client_or_server.get_server_ip(), font_size=20,
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

        # Schedule periodic updates (every 2 seconds)
        arcade.schedule(self.update_player_list, 2.0)

    def update_player_list(self, delta_time=None):
        """Update the player list display to reflect current connected players"""
        try:
            # Check if client_or_server is still valid
            if self.client_or_server is None:
                arcade.unschedule(self.update_player_list)
                return

            # Clear existing player buttons
            self.player_layout.clear()

            # Get current players with timeout protection
            try:
                players = self.client_or_server.get_players()
            except Exception as e:
                print(f"Error getting players: {e}")
                players = []

            # Add player buttons to layout
            for i, player in enumerate(players):
                player_text = f"{player[0]}:{player[1]}"
                player_button = GameButton(text=player_text, width=200, height=50)
                self.player_layout.add(player_button)

        except Exception as e:
            print(f"Error updating player list: {e}")

    def on_back_click(self, event):
        # Unschedule the update function to prevent errors after view change
        arcade.unschedule(self.update_player_list)

        # disconnect from server
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