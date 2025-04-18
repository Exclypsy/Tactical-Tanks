import math
import arcade
import time
from Bullet import Bullet


class Tank(arcade.Sprite):
    """Tank sprite that rotates around its center and can fire bullets."""

    def __init__(self, image_file, bullet_image, scale=1.0, player_id=None):
        super().__init__(image_file, scale)

        # Movement properties
        self.rotation_speed = 90  # degrees per second
        self.is_rotating = False
        self.is_moving = False
        self.speed = 200  # pixels per second
        self.clockwise = True
        self.barrel_length = 80

        # Game properties
        self.player_id = player_id
        self.health = 100
        self.destroyed = False

        # Bullet management
        self.bullet_image = bullet_image
        self.bullet_list = arcade.SpriteList()
        self.last_fire_time = 0
        self.fire_cooldown = 0.5  # SHOOTING COOLDOWN

    def update(self, delta_time: float, window_width=None, window_height=None):
        if self.destroyed:
            return

        # Handle rotation
        if self.is_rotating:
            rotation_amount = self.rotation_speed * delta_time
            self.angle += rotation_amount if self.clockwise else -rotation_amount

        # Handle movement
        if self.is_moving:
            radian_angle = math.radians(self.angle)
            self.center_x += math.sin(radian_angle) * self.speed * delta_time
            self.center_y += math.cos(radian_angle) * self.speed * delta_time

            # Keep within bounds if window dimensions provided
            if window_width and window_height:
                self.center_x = max(0, int(min(self.center_x, window_width)))
                self.center_y = max(0, int(min(self.center_y, window_height)))

        # Update bullets
        self.bullet_list.update(delta_time)

        # Clean up out-of-bounds bullets
        if window_width and window_height:
            self.cleanup_bullets(window_width, window_height)

    def get_barrel_position(self):
        """Returns the position at the end of the barrel"""
        angle_rad = math.radians(self.angle)
        offset_x = math.sin(angle_rad) * self.barrel_length
        offset_y = math.cos(angle_rad) * self.barrel_length
        return self.center_x + offset_x, self.center_y + offset_y

    def fire(self):
        """Fire a bullet if cooldown has elapsed"""
        current_time = time.time()
        if current_time - self.last_fire_time < self.fire_cooldown:
            return None

        self.last_fire_time = current_time

        barrel_x, barrel_y = self.get_barrel_position()
        bullet = Bullet(
            self.bullet_image,
            0.4,
            barrel_x,
            barrel_y,
            self.angle,
            self  # Pass source tank to prevent self-damage
        )

        self.bullet_list.append(bullet)
        return bullet

    def cleanup_bullets(self, window_width, window_height):
        """Remove bullets that have gone off-screen"""
        for bullet in self.bullet_list:
            if (bullet.center_x < 0 or bullet.center_x > window_width or
                    bullet.center_y < 0 or bullet.center_y > window_height):
                bullet.remove_from_sprite_lists()

    def check_bullet_collisions(self, other_tanks):
        """Check for collisions between this tank's bullets and other tanks"""
        hit_tank = None
        for bullet in self.bullet_list:
            for tank in other_tanks:
                if tank != self and not tank.destroyed and arcade.check_for_collision(bullet, tank):
                    bullet.remove_from_sprite_lists()
                    tank.take_damage()
                    hit_tank = tank
                    break
            if hit_tank:
                break
        return hit_tank

    def take_damage(self, damage=100):
        """Handle taking damage"""
        self.health -= damage
        if self.health <= 0:
            self.destroyed = True
        return self.destroyed

    def handle_key_press(self, key, modifiers=None):
        """Handle key press for this tank"""
        if key == arcade.key.SPACE and not self.destroyed:
            self.is_rotating = False
            self.is_moving = True
            return self.fire()
        return None

    def handle_key_release(self, key, modifiers=None):
        """Handle key release for this tank"""
        if key == arcade.key.SPACE:
            self.is_moving = False
            self.is_rotating = True
            self.clockwise = not self.clockwise
