import math

import arcade
class Tank(arcade.Sprite):
    """Tank sprite that rotates around its center."""

    def __init__(self, image_file, scale=1.0):
        super().__init__(image_file, scale)
        self.rotation_speed = 90  # degrees per second
        self.is_rotating = False  # Initialize rotation state
        self.is_moving = False  # Movement state
        self.speed = 200  # Movement speed in pixels per second
        self.clockwise = True  # Track rotation direction

    def update(self, delta_time: float):
        # Rotate if rotating is enabled
        if self.is_rotating:
            # Use direction flag to determine rotation direction
            if self.clockwise:
                self.angle += self.rotation_speed * delta_time
            else:
                self.angle -= self.rotation_speed * delta_time

        # Move forward if moving is enabled
        if self.is_moving:
            # In Arcade, angle 0 points right and increases clockwise
            # We need to adjust our math calculations accordingly
            radian_angle = math.radians(self.angle)

            self.center_x += math.sin(radian_angle) * self.speed * delta_time
            self.center_y += math.cos(radian_angle) * self.speed * delta_time
