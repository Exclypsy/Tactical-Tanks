import arcade
from Tank import Tank


class Game(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Tank Game")
        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Create a sprite list to manage drawing
        self.sprites_list = arcade.SpriteList()

        # Create the tank and add it to the sprite list
        self.tank = Tank("imgs/tank.png", 0.5)
        self.tank.center_x = self.width // 2
        self.tank.center_y = self.height // 2
        self.tank.is_rotating = True
        self.sprites_list.append(self.tank)

    def on_draw(self):
        self.clear()
        # Draw all sprites using the sprite list
        self.sprites_list.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            # Stop rotating and start moving forward
            self.tank.is_rotating = False
            self.tank.is_moving = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.SPACE:
            # Stop moving forward and resume rotating
            self.tank.is_moving = False
            self.tank.is_rotating = True
            # Reverse rotation direction when tank stops
            self.tank.clockwise = not self.tank.clockwise

    def on_update(self, delta_time):
        # Update all sprites in the sprite list
        self.sprites_list.update()


def main():
    game = Game()
    arcade.run()


if __name__ == "__main__":
    main()
