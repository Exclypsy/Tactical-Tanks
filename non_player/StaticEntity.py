import arcade
import random

class StaticEntity(arcade.Sprite):
    """
    A general-purpose static (non-moving) entity class for game objects like trees, rocks, walls, etc.
    Supports different entity types, customizable health, and automatic hitbox calculation.
    """

    # Class-level asset mapping for different entity types
    ENTITY_ASSETS = {
        "bush_small": ":assets:images/static_entities/bush_small.png",
        "bush_big": ":assets:images/static_entities/bush_big.png",
        "rock0": ":assets:images/static_entities/rock0.png",
        "rock1": ":assets:images/static_entities/rock1.png",
        "rock2": ":assets:images/static_entities/rock2.png",
        "rock3": ":assets:images/static_entities/rock3.png",
        # Add more entity types as needed
    }

    # Class-level sound cache for optimization
    _destroy_sound = None

    def __init__(self, x_pos, y_pos, entity_type="bush_big", hp=3, scale=1.0, rotation=0):
        """
        Initialize a static entity.
        Args:
            x_pos (float): X position on the screen
            y_pos (float): Y position on the screen
            entity_type (str): Type of entity (tree, bush, rock, wall, etc.)
            hp (int): Hit points (0 = indestructible, >0 = destructible)
            scale (float): Scale factor for the sprite (1.0 = original size)
            rotation (float): Rotation angle in degrees
        """
        # Get the appropriate image for the entity type
        image_path = self.ENTITY_ASSETS.get(entity_type, self.ENTITY_ASSETS["bush_big"])
        super().__init__(image_path, scale)

        # Set position and properties
        self.center_x = x_pos
        self.center_y = y_pos
        self.angle = rotation
        self.entity_type = entity_type
        self.max_hp = hp
        self.current_hp = hp
        self.is_indestructible = (hp == 0)

        # Load destroy sound once per class (optimization)
        if StaticEntity._destroy_sound is None:
            StaticEntity._destroy_sound = arcade.load_sound(":assets:sounds/hush.mp3")

    def update(self, bullet_list, effects_manager=None):
        """
        Handle collision detection with bullets.
        Args:
            bullet_list: List or SpriteList of bullets to check collision against
            effects_manager: Effects manager for creating explosion effects
        """
        # Check for collisions with bullets (ALWAYS check, even for indestructible)
        hit_list = arcade.check_for_collision_with_list(self, bullet_list)

        for bullet in hit_list:
            # Create explosion effect if effects_manager is provided
            if effects_manager is not None:
                from client.assets.effects.ExplosionEffect import ExplosionEffect
                explosion = ExplosionEffect(bullet.center_x, bullet.center_y)
                effects_manager.add_effect(explosion)

            # Always remove bullet on collision (even with indestructible entities)
            bullet.remove_from_sprite_lists()

            # Only deal damage to destructible entities
            if not self.is_indestructible:
                # Get damage from bullet if available, otherwise default to 1
                damage = getattr(bullet, 'damage', 1)
                # Deal damage and check if entity was destroyed
                if self.take_damage(damage):
                    break  # Entity destroyed, no need to process more bullets

    def take_damage(self, damage=1):
        """
        Deal damage to the entity and handle destruction.
        Args:
            damage (int): Amount of damage to deal
        Returns:
            bool: True if entity was destroyed, False if it survived
        """
        if self.is_indestructible:
            return False

        self.current_hp -= damage
        print(f"Entity {self.entity_type} took {damage} damage. HP: {self.current_hp}/{self.max_hp}")

        if self.current_hp <= 0:
            self.destroy()
            return True  # Entity was destroyed

        return False  # Entity survived

    def destroy(self):
        """Handle entity destruction with sound and cleanup."""
        print(f"Entity {self.entity_type} destroyed!")
        arcade.play_sound(StaticEntity._destroy_sound)
        self.remove_from_sprite_lists()

    def is_alive(self):
        """Check if entity is still alive or indestructible."""
        return self.current_hp > 0 or self.is_indestructible

    def get_health_percentage(self):
        """Get current health as a percentage (useful for health bars)."""
        if self.is_indestructible:
            return 100.0
        return (self.current_hp / self.max_hp) * 100.0

    @classmethod
    def create_random_entity(cls, window_width, window_height, entity_types=None,
                           min_hp=2, max_hp=5, min_scale=0.3, max_scale=0.8,
                           border_margin=50):
        """
        Factory method to create a random entity (useful for procedural level generation).
        Args:
            window_width (int): Game window width
            window_height (int): Game window height
            entity_types (list): List of entity types to choose from
            min_hp, max_hp (int): HP range for random entities (increased defaults)
            min_scale, max_scale (float): Scale range for random entities
            border_margin (int): Margin from screen edges
        Returns:
            StaticEntity: A randomly generated entity
        """
        if entity_types is None:
            entity_types = ["bush_small", "bush_big", "rock0", "rock1"]

        return cls(
            x_pos=random.randint(border_margin, window_width - border_margin),
            y_pos=random.randint(border_margin, window_height - border_margin),
            entity_type=random.choice(entity_types),
            hp=random.randint(min_hp, max_hp),
            scale=random.uniform(min_scale, max_scale),
            rotation=random.randint(0, 360)
        )
