import math

from pygame import Vector2

from tanky.Bullet import Bullet
import pygame

from tanky.structure import BLACK


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, color, player_id):
        super().__init__()


        self.original_image = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.original_image, color, (0, 0, 30, 40))

        pygame.draw.rect(self.original_image, BLACK, (10, 0, 10, 20))

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))


        self.position = Vector2(x, y)
        self.direction = Vector2(0, -1)
        self.speed = 3


        self.angle = 0
        self.rotation_speed = 2
        self.spinning = True
        self.clockwise = True


        self.bullet = None


        self.player_id = player_id

    def update(self):
        if self.spinning:
            # Rotate the tank
            if self.clockwise:
                self.angle += self.rotation_speed
            else:
                self.angle -= self.rotation_speed


            self.angle %= 360


            self.direction.x = math.sin(math.radians(self.angle))
            self.direction.y = -math.cos(math.radians(self.angle))

            # Rotate the tank image
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)
        else:
            # Move in the current direction if not spinning
            self.position += self.direction * self.speed
            self.rect.center = self.position

    def handle_spacebar(self):
        if self.spinning:
            # Stop spinning and start moving
            self.spinning = False
            # Fire a bullet
            self.shoot()
        else:
            # Start spinning again but reverse direction
            self.spinning = True
            self.clockwise = not self.clockwise

    def shoot(self):
        # Create a bullet at the tank's position, moving in the tank's direction
        bullet_pos = self.position + self.direction * 20  # Start bullet away from tank center
        self.bullet = Bullet(bullet_pos.x, bullet_pos.y, self.direction, self.player_id)
        return self.bullet
