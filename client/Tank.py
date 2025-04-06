import math
import arcade
from arcade.hitbox import calculate_hit_box_points_simple, HitBox


class Tank(arcade.Sprite):
    """Tank sprite that rotates around its center."""

    def __init__(self, image_file, scale=1.0):
        # Call the parent class initializer first
        super().__init__(image_file, scale)
        self.rotation_speed = 90  # degrees per second
        self.is_rotating = False  # Initialize rotation state
        self.is_moving = False  # Movement state
        self.speed = 200  # Movement speed in pixels per second
        self.clockwise = True  # Track rotation direction
        self.barrel_length = 80


    # Rest of your methods remain the same
    def update(self, delta_time: float):
        # Rotate if rotating is enabled
        if self.is_rotating:
            # Use direction flag to determine rotation direction
            if self.clockwise:
                self.angle += self.rotation_speed * delta_time
            else:
                self.angle -= self. rotation_speed * delta_time

        # Move forward if moving is enabled
        if self.is_moving:
            # In Arcade, angle 0 points right and increases clockwise
            # We need to adjust our math calculations accordingly
            radian_angle = math.radians(self.angle)
            self.center_x += math.sin(radian_angle) * self.speed * delta_time
            self.center_y += math.cos(radian_angle) * self.speed * delta_time

    def get_barrel_position(self):
        """Returns the position at the end of the barrel   """
        angle_rad = math.radians(self.angle)
        offset_x = math.sin(angle_rad) * self.barrel_length
        offset_y = math.cos(angle_rad) * self.barrel_length

        return self.center_x + offset_x, self.center_y + offset_y
