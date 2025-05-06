import arcade
import random

class Tree(arcade.Sprite):
    def __init__(self, image_path, scale=0.3):
        super().__init__(image_path, scale)
        self.center_x = random.randint(50, 750)  # Random x position
        self.center_y = random.randint(50, 550)  # Random y position
