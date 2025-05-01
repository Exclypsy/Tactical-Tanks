from pathlib import Path

import arcade
from client.Tank import Tank

project_root = Path(__file__).resolve().parent.parent
path = project_root / "client" / "assets"
arcade.resources.add_resource_handle("assets", str(path.resolve()))

class GameView(arcade.View):
    def __init__(self, window, client_or_server, is_client):
        super().__init__()
        self.window = window
        # self.window.maximize()

        self.client_or_server = client_or_server
        self.is_client = is_client

        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Create tank list
        self.tanks = arcade.SpriteList()

        # Create the player tank
        self.player_tank = Tank(
            ":assets:images/tank.png",
    ":assets:images/bullet.png",
            0.5,
            player_id="player1"
        )
        self.player_tank.center_x = self.width // 2
        self.player_tank.center_y = self.height // 2
        self.player_tank.is_rotating = True
        self.tanks.append(self.player_tank)



        # Debug flags
        self.show_hitboxes = False
        self.game_over = False

    def on_resize(self, width, height):
        """Handle window resizing events"""
        super().on_resize(width, height)

        # Reposition the player tank
        self.player_tank.center_x = width // 2
        self.player_tank.center_y = height // 2

    def on_draw(self):
        self.clear()

        # Draw all bullets from all tanks
        for tank in self.tanks:
            tank.bullet_list.draw()

        # Draw tanks
        self.tanks.draw()

        # DEBUG
        # Draw debug direction line for player tank
        self.player_tank.draw_debug_direction_line(self.width, self.height)

        # Draw hitboxes for debugging
        if self.show_hitboxes:
            for tank in self.tanks:
                tank.bullet_list.draw_hit_boxes(arcade.color.RED)
            self.tanks.draw_hit_boxes(arcade.color.GREEN)

        if self.game_over:
            arcade.draw_text("GAME OVER - TANK DESTROYED!",
                             self.width / 2, self.height / 2,
                             arcade.color.RED, 24, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if self.game_over:
            return

        if key == arcade.key.SPACE:
            self.player_tank.handle_key_press(key)
        elif key == arcade.key.H:
            self.show_hitboxes = not self.show_hitboxes

    def on_key_release(self, key, modifiers):
        if not self.game_over and key == arcade.key.SPACE:
            self.player_tank.handle_key_release(key)


    def on_update(self, delta_time):
        if self.game_over:
            return

        # Update all tanks
        for tank in self.tanks:
            tank.update(delta_time, self.width, self.height)

            # Check for bullet collisions with other tanks
            hit_tank = tank.check_bullet_collisions([t for t in self.tanks if t != tank])
            if hit_tank and hit_tank == self.player_tank and hit_tank.destroyed:
                self.game_over = True
