import arcade
import time
from Tank import Tank


class Game(arcade.Window):
    def __init__(self):
        # Create a resizable window
        super().__init__(800, 600, "Tank Game", resizable=True)
        self.maximize()
        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Create tank list
        self.tanks = arcade.SpriteList()

        # Create the player tank
        self.player_tank = Tank(
            "assets/images/tank.png",
            "assets/images/bullet.png",
            0.5,
            player_id="player1"
        )
        self.player_tank.center_x = self.width // 2
        self.player_tank.center_y = self.height // 2
        self.player_tank.is_rotating = True
        self.tanks.append(self.player_tank)

        # Test bullet spawning
        self.last_test_bullet_time = time.time()
        self.bullet_spawn_interval = 2.0  # seconds

        # Create enemy tank for test bullets
        self.enemy_tank = Tank(
            "assets/images/tank.png",
            "assets/images/bullet.png",
            0.5,
            player_id="enemy"
        )
        self.enemy_tank.center_x = -100  # Off-screen
        self.enemy_tank.center_y = self.height // 2
        self.enemy_tank.angle = 90  # Pointing right

        # Debug flags
        self.show_hitboxes = True
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

        # Draw enemy tank bullets for testing
        self.enemy_tank.bullet_list.draw()

        # Draw tanks
        self.tanks.draw()

        # Draw hitboxes for debugging
        if self.show_hitboxes:
            for tank in self.tanks:
                tank.bullet_list.draw_hit_boxes(arcade.color.RED)
            self.enemy_tank.bullet_list.draw_hit_boxes(arcade.color.RED)
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

    def spawn_test_bullet(self):
        """Spawn a test bullet from the left side of the screen"""
        self.enemy_tank.center_y = self.height // 2
        bullet = self.enemy_tank.fire()
        if bullet:
            # Position bullet at left edge
            bullet.center_x = 0
            bullet.center_y = self.height // 2

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

        # Update enemy tank for test bullets
        self.enemy_tank.update(delta_time, self.width, self.height)

        # Check enemy bullets hitting player tanks
        hit_tank = self.enemy_tank.check_bullet_collisions(self.tanks)
        if hit_tank and hit_tank.destroyed and hit_tank == self.player_tank:
            self.game_over = True

        # Spawn test bullets periodically
        current_time = time.time()
        if current_time - self.last_test_bullet_time >= self.bullet_spawn_interval:
            self.spawn_test_bullet()
            self.last_test_bullet_time = current_time


def main():
    game = Game()
    arcade.run()


if __name__ == "__main__":
    main()
