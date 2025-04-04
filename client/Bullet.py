import math
import arcade
from arcade.hitbox import calculate_hit_box_points_simple, HitBox


class Bullet(arcade.Sprite):
    """Bullet sprite that travels in a straight line at constant speed."""

    def __init__(self, image_file, scale=1.0, start_x=0, start_y=0, angle=0, source_tank=None):
        """Initialize the bullet with position and direction from the tank.

        Args:
            image_file: Path to the bullet image
            scale: Size scaling factor
            start_x: Starting x-position
            start_y: Starting y-position
            angle: Direction angle in degrees
            source_tank: Reference to the tank that fired this bullet
        """
        super().__init__(image_file, scale)

        # Set initial position
        self.center_x = start_x
        self.center_y = start_y

        # Set angle matching the tank's direction
        self.angle = angle

        # Bullet speed (pixels per second)
        self.speed = 800

        # Store the initial direction vector
        self.direction_radians = math.radians(self.angle)

        # Store reference to the source tank
        self.source_tank = source_tank


    def update(self, delta_time: float):
        """Update bullet position based on constant direction and speed."""
        # Calculate movement distance for this frame
        distance = self.speed * delta_time

        # Update position using the fixed direction
        self.center_x += math.sin(self.direction_radians) * distance
        self.center_y += math.cos(self.direction_radians) * distance
