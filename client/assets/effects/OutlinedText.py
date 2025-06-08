import arcade
import pyglet
import math
from typing import List, Optional, Tuple


class OutlinedText:
    """
    High-performance outlined text class with smooth circular outlines.
    Manages its own batch and text objects for optimal performance.
    """

    def __init__(self, text: str, x: float, y: float,
                 text_color: Tuple[int, int, int] = arcade.color.WHITE,
                 outline_color: Tuple[int, int, int] = arcade.color.BLACK,
                 font_size: float = 24, stroke_width: int = 2,
                 anchor_x: str = "center", anchor_y: str = "center",
                 num_outline_points: int = 16, font_name="ARCO",  batch: Optional[pyglet.graphics.Batch] = None):
        """
        Initialize outlined text with all configurable parameters.

        Args:
            text: The text string to display
            x, y: Position coordinates
            text_color: RGB color tuple for main text
            outline_color: RGB color tuple for outline
            font_size: Font size in points
            stroke_width: Outline thickness in pixels
            anchor_x, anchor_y: Text anchoring
            num_outline_points: Smoothness of circular outline
            batch: Optional external batch (creates own if None)
        """
        self.text = text
        self.x = x
        self.y = y
        self.text_color = text_color
        self.outline_color = outline_color
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.font_name = font_name
        self.num_outline_points = num_outline_points

        # Create batch if not provided
        self.external_batch = batch is not None
        self.batch = batch if batch else pyglet.graphics.Batch()

        # Store text objects
        self.text_objects: List[arcade.Text] = []

        # Create the outlined text
        self._create_text_objects()

    def _generate_circular_offsets(self) -> List[Tuple[int, int]]:
        """Generate smooth circular offsets for outline."""
        offsets = []
        if self.stroke_width > 0:
            for i in range(self.num_outline_points):
                angle = (2 * math.pi * i) / self.num_outline_points
                x_offset = int(self.stroke_width * math.cos(angle))
                y_offset = int(self.stroke_width * math.sin(angle))
                offsets.append((x_offset, y_offset))
        return offsets

    def _create_text_objects(self):
        """Create all text objects (outline + main text)."""
        self.text_objects.clear()

        # Create outline objects
        outline_offsets = self._generate_circular_offsets()
        for offset_x, offset_y in outline_offsets:
            outline_text = arcade.Text(
                self.text, self.x + offset_x, self.y + offset_y,
                self.outline_color, self.font_size,
                anchor_x=self.anchor_x, anchor_y=self.anchor_y,
                batch=self.batch, font_name=self.font_name
            )
            self.text_objects.append(outline_text)

        # Create main text object
        main_text = arcade.Text(
            self.text, self.x, self.y, self.text_color, self.font_size,
            anchor_x=self.anchor_x, anchor_y=self.anchor_y,
            batch=self.batch, font_name=self.font_name
        )
        self.text_objects.append(main_text)

    def update_text(self, new_text: str):
        """Update the displayed text."""
        self.text = new_text
        self._create_text_objects()

    def update_position(self, x: float, y: float):
        """Move the text to a new position."""
        self.x = x
        self.y = y
        self._create_text_objects()

    def update_colors(self, text_color: Tuple[int, int, int],
                      outline_color: Tuple[int, int, int]):
        """Change text and outline colors."""
        self.text_color = text_color
        self.outline_color = outline_color
        self._create_text_objects()

    def update_stroke_width(self, stroke_width: int):
        """Change outline thickness."""
        self.stroke_width = stroke_width
        self._create_text_objects()

    def draw(self):
        """Draw the outlined text (only needed if not using external batch)."""
        if not self.external_batch:
            self.batch.draw()

    def get_batch(self) -> pyglet.graphics.Batch:
        """Get the internal batch for external batch management."""
        return self.batch
