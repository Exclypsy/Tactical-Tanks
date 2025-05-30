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

    def __init__(self, x_pos, y_pos, entity_type="bush", hp=1, scale=1.0, rotation=0):
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
        image_path = self.ENTITY_ASSETS.get(entity_type, self.ENTITY_ASSETS["bush"])

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

        # Arcade automatically calculates hitbox based on texture using the newest algorithm
        # The hitbox will be calculated based on the actual image shape
        # For more precise hitboxes, arcade uses the texture's alpha channel

    def update(self, bullet_list):
        """
        Handle collision detection with bullets.

        Args:
            bullet_list: List or SpriteList of bullets to check collision against
        """
        # Skip collision detection for indestructible entities (optimization)
        if self.is_indestructible:
            return

        # Check for collisions with bullets
        hit_list = arcade.check_for_collision_with_list(self, bullet_list)
        for bullet in hit_list:
            # Remove bullet and deal damage
            bullet.remove_from_sprite_lists()

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

        if self.current_hp <= 0:
            self.destroy()
            return True  # Entity was destroyed
        return False  # Entity survived

    def destroy(self):
        """Handle entity destruction with sound and cleanup."""
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
                             min_hp=1, max_hp=3, min_scale=0.3, max_scale=0.8,
                             border_margin=50):
        """
        Factory method to create a random entity (useful for procedural level generation).

        Args:
            window_width (int): Game window width
            window_height (int): Game window height
            entity_types (list): List of entity types to choose from
            min_hp, max_hp (int): HP range for random entities
            min_scale, max_scale (float): Scale range for random entities
            border_margin (int): Margin from screen edges

        Returns:
            StaticEntity: A randomly generated entity
        """
        if entity_types is None:
            entity_types = ["tree", "bush", "rock"]

        return cls(
            x_pos=random.randint(border_margin, window_width - border_margin),
            y_pos=random.randint(border_margin, window_height - border_margin),
            entity_type=random.choice(entity_types),
            hp=random.randint(min_hp, max_hp),
            scale=random.uniform(min_scale, max_scale),
            rotation=random.randint(0, 360)
        )


class EntityManager:
    """
    Optional manager class for handling multiple static entities efficiently.
    Groups entities by type for optimized rendering and collision detection.
    """

    def __init__(self):
        self.entity_lists = {}  # Dict of SpriteList by entity type
        self.all_entities = arcade.SpriteList()

    def add_entity(self, entity):
        """Add an entity to the manager."""
        entity_type = entity.entity_type

        # Create sprite list for this type if it doesn't exist
        if entity_type not in self.entity_lists:
            self.entity_lists[entity_type] = arcade.SpriteList()

        self.entity_lists[entity_type].append(entity)
        self.all_entities.append(entity)

    def update(self, bullet_list):
        """Update all entities with collision detection."""
        for entity in self.all_entities:
            entity.update(bullet_list)

    def draw(self):
        """Draw all entities, grouped by type for optimization."""
        for sprite_list in self.entity_lists.values():
            sprite_list.draw()

    def draw_hit_boxes(self, color=arcade.color.RED):
        """Draw hitboxes for debugging."""
        self.all_entities.draw_hit_boxes(color)

    def get_entities_by_type(self, entity_type):
        """Get all entities of a specific type."""
        return self.entity_lists.get(entity_type, arcade.SpriteList())

    def remove_destroyed_entities(self):
        """Clean up destroyed entities from all lists."""
        for entity_list in self.entity_lists.values():
            for entity in entity_list:
                if not entity.is_alive():
                    entity.remove_from_sprite_lists()
