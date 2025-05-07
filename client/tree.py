import arcade
import random

class Tree(arcade.Sprite):
    def __init__(self):
        super().__init__(":assets:images/tree1.png")
        self.scale = 0.15
        self.center_x = random.randint(50, 750)
        self.center_y = random.randint(50, 550)
        self.health = random.randint(2, 5)  # Each tree gets 2–5 health points

    def update(self, bullet_list):
        hit_list = arcade.check_for_collision_with_list(self, bullet_list)
        for bullet in hit_list:
            bullet.remove_from_sprite_lists()
            self.health -= 1
            if self.health <= 0:
                self.remove_from_sprite_lists()
                break
