import arcade
from Tank import Tank
from Bullet import Bullet
import time


class Game(arcade.Window):
    def __init__(self):
        # Create a resizable window
        super().__init__(800, 600, "Tank Game", resizable=True)

        # Maximize the window after creation
        self.maximize()

        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Create sprite lists
        self.tankList = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Create the tank and add it to the sprite list
        self.tank = Tank("imgs/tank.png", 0.5)
        self.tank.center_x = self.width // 2
        self.tank.center_y = self.height // 2
        self.tank.is_rotating = True
        self.tankList.append(self.tank)

        # Add timer for auto-spawning test bullets
        self.last_bullet_time = time.time()
        self.bullet_spawn_interval = 2.0  # 2 seconds

        # Flag to show hitboxes for debugging
        self.show_hitboxes = True
        self.game_over = False

    def on_resize(self, width, height):
        """Handle window resizing events"""
        # Call the parent implementation first
        super().on_resize(width, height)

        # Reposition the tank to maintain center position when window resizes
        if hasattr(self, 'tank'):
            self.tank.center_x = width // 2
            self.tank.center_y = height // 2

    def on_draw(self):
        self.clear()
        # Draw bullets first so they appear behind tanks
        self.bullet_list.draw()
        # Draw tanks on top of bullets
        self.tankList.draw()

        # Draw hitboxes for debugging
        if self.show_hitboxes:
            self.bullet_list.draw_hit_boxes(arcade.color.RED)
            self.tankList.draw_hit_boxes(arcade.color.GREEN)

        if self.game_over:
            arcade.draw_text("GAME OVER - TANK DESTROYED!",
                             self.width / 2, self.height / 2,
                             arcade.color.RED, 24, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and not self.game_over:
            # Stop rotating and start moving forward
            self.tank.is_rotating = False
            self.tank.is_moving = True

            # Create a bullet and add it to the bullet list
            bullet = Bullet(
                "imgs/bullet.png",
                0.4,
                self.tank.get_barrel_position()[0],
                self.tank.get_barrel_position()[1],
                self.tank.angle,
                self.tank  # Pass source tank to prevent self-damage
            )
            self.bullet_list.append(bullet)
        # Toggle hitbox display with 'H' key
        elif key == arcade.key.H:
            self.show_hitboxes = not self.show_hitboxes

    def on_key_release(self, key, modifiers):
        if key == arcade.key.SPACE:
            # Stop moving forward and resume rotating
            self.tank.is_moving = False
            self.tank.is_rotating = True
            # Reverse rotation direction when tank stops
            self.tank.clockwise = not self.tank.clockwise

    def spawn_test_bullet(self):
        """Spawn a bullet from the left side moving right for hitbox testing"""
        bullet = Bullet(
            "imgs/bullet.png",
            0.4,
            0,  # Start at the left edge
            self.height // 2,  # Center height
            90,  # Angle pointing right
            None  # No source tank - will collide with player tank
        )
        self.bullet_list.append(bullet)

    def on_update(self, delta_time):
        if self.game_over:
            return

        # Update all sprites in the sprite list
        self.tankList.update()

        # Update bullets
        self.bullet_list.update(delta_time)

        # Check for collisions between bullets and tanks
        for bullet in self.bullet_list:
            for tank in self.tankList:
                # Skip collision check if this is the source tank (no self-damage)
                if tank != bullet.source_tank and arcade.check_for_collision(bullet, tank):
                    print("Bullet hit tank! Game Over.")
                    self.game_over = True
                    return

        # Remove bullets that have gone off-screen
        for bullet in self.bullet_list:
            if (bullet.center_x < 0 or bullet.center_x > self.width or
                    bullet.center_y < 0 or bullet.center_y > self.height):
                bullet.remove_from_sprite_lists()

        # Check if it's time to spawn a new test bullet
        current_time = time.time()
        if current_time - self.last_bullet_time >= self.bullet_spawn_interval:
            self.spawn_test_bullet()
            self.last_bullet_time = current_time


def main():
    game = Game()
    arcade.run()


if __name__ == "__main__":
    main()
