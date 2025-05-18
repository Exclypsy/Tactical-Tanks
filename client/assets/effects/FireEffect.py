# Add to your imports at the top
import time

from arcade.sprite import Sprite

class FireEffect(Sprite):
    def __init__(self, image_file, scale, x, y, angle):
        super().__init__(image_file, scale)
        self.center_x = x
        self.center_y = y
        self.angle = angle
        self.creation_time = time.time()
        self.lifetime = 0.15  # Effect lasts for 150ms

    def update(self):
        # Check if the effect should be removed
        if time.time() - self.creation_time > self.lifetime:
            self.remove_from_sprite_lists()
