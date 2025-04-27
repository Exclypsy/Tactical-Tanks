import arcade
from arcade.gui import UIView, UIAnchorLayout
from pathlib import Path
from GameButton import GameButton


class LobbyView(UIView):
    def __init__(self, window):
        super().__init__()
        self.window = window

        # Set background color
        self.background_color = arcade.color.PURPLE

        # Load background image with radial pattern
        project_root = Path(__file__).resolve().parent
        path = project_root / "client" / "assets"
        arcade.resources.add_resource_handle("assets", str(path.resolve()))
        self.background = arcade.load_texture(":assets:images/background.png")

        # Load tank texture
        self.tank_texture = arcade.load_texture(":assets:images/tank.png")

        # Create start game button
        start_button = GameButton(text="START GAME", width=200, height=60)
        start_button.on_click = self.on_start_game

        # Add START GAME button
        bottom_anchor = UIAnchorLayout()
        bottom_anchor.add(
            child=start_button,
            anchor_x="center",
            anchor_y="bottom",
            align_y=40
        )
        self.ui.add(bottom_anchor)

    def on_start_game(self, event):
        # Handle start game button click
        pass

    def on_draw_before_ui(self):
        # Draw background - using draw_texture_rect instead of draw_texture_rectangle
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, self.width, self.height),
        )

        # Draw server info at the top
        self.draw_text_with_stroke(
            "SERVER: 192.168.1.1:8080",
            self.width / 2,
            self.height - 40,
            arcade.color.WHITE,
            28,
            True
        )

        # Calculate positions for player boxes
        total_width = 4 * 120 + 3 * 40  # 4 boxes + 3 spaces
        start_x = (self.width - total_width) / 2 + 60  # center of first box
        center_y = self.height / 2

        # Draw player boxes
        for i in range(4):
            center_x = start_x + i * (120 + 40)

            # Draw blue box
            arcade.draw_rectangle_filled(
                center_x=center_x,
                center_y=center_y,
                width=120,
                height=120,
                color=arcade.color.CORNFLOWER_BLUE
            )

            # Draw white border
            arcade.draw_rectangle_outline(
                center_x=center_x,
                center_y=center_y,
                width=120,
                height=120,
                color=arcade.color.WHITE,
                border_width=4
            )

            # Draw diagonal "TANK.PNG" text
            arcade.draw_text(
                "TANK.PNG",
                center_x,
                center_y,
                arcade.color.WHITE,
                font_size=20,
                anchor_x="center",
                anchor_y="center",
                rotation=45,
                bold=True
            )

            # Draw player name with stroke
            self.draw_text_with_stroke(
                "PLAYER NAME",
                center_x,
                center_y - 80,
                arcade.color.WHITE,
                18,
                True
            )

            # Draw IP with stroke
            self.draw_text_with_stroke(
                "192.168.1.127",
                center_x,
                center_y - 110,
                arcade.color.WHITE,
                14
            )

    def draw_text_with_stroke(self, text, x, y, color, font_size, bold=False):
        # Draw black stroke outline
        stroke_width = 2
        for offset_x, offset_y in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            arcade.draw_text(
                text,
                x + (offset_x * stroke_width),
                y + (offset_y * stroke_width),
                arcade.color.BLACK,
                font_size,
                anchor_x="center",
                anchor_y="center",
                bold=bold
            )

        # Draw the main text
        arcade.draw_text(
            text,
            x,
            y,
            color,
            font_size,
            anchor_x="center",
            anchor_y="center",
            bold=bold
        )


# Main entry point
if __name__ == "__main__":
    window = arcade.Window(1024, 768, "Tank Game Lobby")
    lobby_view = LobbyView(window)
    window.show_view(lobby_view)
    arcade.run()
