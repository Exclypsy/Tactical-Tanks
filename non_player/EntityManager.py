import arcade


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

    def update(self, bullet_list, effects_manager=None):
        """Update all entities with collision detection."""
        for entity in self.all_entities:
            entity.update(bullet_list, effects_manager)

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
