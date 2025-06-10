import math
import arcade


class Bullet(arcade.Sprite):
    """Bullet sprite that travels in a straight line at constant speed.
    Supports collision with other bullets."""

    def __init__(self, image_file, scale=1.0, start_x=0, start_y=0, angle=0, source_tank=None):
        super().__init__(image_file, scale)

        # Position and direction
        self.center_x = start_x
        self.center_y = start_y
        self.angle = angle

        # Movement properties
        self.speed = 800  # pixels per second
        self.direction_radians = math.radians(self.angle)

        # Game properties
        self.source_tank = source_tank
        self.damage = 1

    def update(self, delta_time: float):
        """Update bullet position based on constant direction and speed."""
        distance = self.speed * delta_time
        self.center_x += math.sin(self.direction_radians) * distance
        self.center_y += math.cos(self.direction_radians) * distance

    def is_out_of_bounds(self, window_width, window_height):
        """Check if bullet is outside the game window"""
        return (self.center_x < 0 or self.center_x > window_width or
                self.center_y < 0 or self.center_y > window_height)

    def check_collision_with_bullets(self, bullet_list):
        """Check for collision with other bullets. If collided, both should be removed."""
        for bullet in bullet_list:
            if bullet is not self and self.collides_with_sprite(bullet):
                bullet.remove_from_sprite_lists()
                self.remove_from_sprite_lists()
                break
