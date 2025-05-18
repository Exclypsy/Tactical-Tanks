import math
import arcade
import time
from client.Bullet import Bullet
from client.assets.effects.FireEffect import FireEffect


class Tank(arcade.Sprite):

    def __init__(self, tank_color="blue", bullet_type="normal", scale=0.5, player_id=None):
        self.tank_color = tank_color
        self.bullet_type = bullet_type

        if self.tank_color == "blue":
            self.tank_texture= ":assets:images/tanks/blue_tank.png"
        elif self.tank_color == "green":
            self.tank_texture = ":assets:images/tanks/green_tank.png"
        elif self.tank_color == "red":
            self.tank_texture = ":assets:images/tanks/red_tank.png"
        elif self.tank_color == "yellow":
            self.tank_texture = ":assets:images/tanks/yellow_tank.png"

        super().__init__(self.tank_texture, scale)


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
        self.bullet_type = bullet_type
        self.bullet_list = arcade.SpriteList()
        self.last_fire_time = 0
        self.fire_cooldown = 0.5  # SHOOTING COOLDOWN

        # Recoil properties
        self.is_recoiling = False
        self.recoil_start_time = 0
        self.recoil_duration = 0.2
        self.recoil_distance = 170

        if self.bullet_type == "normal":
            self.bullet_image = ":assets:images/bullet.png"

        self.shot_sound = arcade.load_sound(":assets:sounds/shot.mp3")

        self.effects_list = arcade.SpriteList()

    def update(self, delta_time: float, window_width=None, window_height=None):
        if self.destroyed:
            return

        for effect in self.effects_list:
            effect.update()

        # Handle recoil if active
        if hasattr(self, 'is_recoiling') and self.is_recoiling:
            current_time = time.time()
            elapsed = current_time - self.recoil_start_time

            if elapsed < self.recoil_duration:
                # Move in the opposite direction of the barrel
                angle_rad = math.radians(self.angle + 180)  # Opposite direction

                # Calculate smooth ease-out effect
                progress = elapsed / self.recoil_duration
                ease_factor = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out

                # Apply recoil movement
                recoil_speed = (self.recoil_distance / self.recoil_duration) * (1 - ease_factor)
                self.center_x += recoil_speed * math.sin(angle_rad) * delta_time
                self.center_y += recoil_speed * math.cos(angle_rad) * delta_time
            else:
                # End recoil
                self.is_recoiling = False

        # Regular movement code continues below...
        if self.is_rotating:
            if self.clockwise:
                self.angle += self.rotation_speed * delta_time
            else:
                self.angle -= self.rotation_speed * delta_time

        if self.is_moving:
            angle_rad = math.radians(self.angle)
            self.center_x += self.speed * math.sin(angle_rad) * delta_time
            self.center_y += self.speed * math.cos(angle_rad) * delta_time

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

        arcade.play_sound(self.shot_sound)

        # Initialize recoil effect
        self.is_recoiling = True
        self.recoil_start_time = current_time


        # Get barrel position
        barrel_x, barrel_y = self.get_barrel_position()

        # Create fire effect at barrel end but slightly farther out
        angle_rad = math.radians(self.angle)
        fire_distance = 40  # pixels beyond barrel end
        fire_x = barrel_x + math.sin(angle_rad) * fire_distance
        fire_y = barrel_y + math.cos(angle_rad) * fire_distance

        fire_effect = FireEffect(":assets:images/fire.png", 0.5, fire_x, fire_y, self.angle)
        self.effects_list.append(fire_effect)

        # Create and return the bullet
        bullet = Bullet(
            self.bullet_image,
            0.55,
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
