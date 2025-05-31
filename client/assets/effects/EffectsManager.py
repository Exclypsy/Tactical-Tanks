import arcade


class EffectsManager:
    def __init__(self):
        self.effects_list = arcade.SpriteList()

    def add_effect(self, effect):
        self.effects_list.append(effect)

    def update(self, delta_time):
        finished_effects = []
        for effect in self.effects_list:
            effect.update(delta_time)
            if hasattr(effect, 'is_animation_finished') and effect.is_animation_finished():
                finished_effects.append(effect)

        for effect in finished_effects:
            effect.remove_from_sprite_lists()

    def draw(self):
        self.effects_list.draw()
