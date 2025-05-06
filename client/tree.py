import arcade
import random

class Tree(arcade.Sprite):
    def __init__(self):
        super().__init__(":assets:images/tree1.png")
        self.scale = 0.15
        self.center_x = random.randint(50, 750)
        self.center_y = random.randint(50, 550)
