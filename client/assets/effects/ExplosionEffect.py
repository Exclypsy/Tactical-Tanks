import arcade


class ExplosionEffect(arcade.Sprite):
    """Simple frame-based explosion effect"""

    def __init__(self, x, y, scale=1.2):
        super().__init__()

        # Position the explosion
        self.center_x = x
        self.center_y = y
        self.scale = scale

        # Load explosion textures
        self.explosion_textures = []
        for i in range(5):
            try:
                texture = arcade.load_texture(f":assets:images/vybuch/hit/hit{i}.png")
                self.explosion_textures.append(texture)
            except FileNotFoundError:
                texture = arcade.load_texture(":assets:images/vybuch/hit/hit2.png")
                self.explosion_textures.append(texture)

        # Animation state
        self.current_frame = 0
        self.frame_duration = 0.08
        self.frame_timer = 0.0
        self.is_finished = False

        # Set initial texture
        self.texture = self.explosion_textures[0]

    def update(self, delta_time: float = 1 / 60):
        """Update the explosion animation"""
        if self.is_finished:
            return

        # Update frame timer
        self.frame_timer += delta_time

        # Check if it's time for next frame
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.current_frame += 1

            # Check if animation is complete
            if self.current_frame >= len(self.explosion_textures):
                self.is_finished = True
                self.alpha = 0  # Make invisible
                self.remove_from_sprite_lists()
                return

            # Update texture to next frame
            self.texture = self.explosion_textures[self.current_frame]

