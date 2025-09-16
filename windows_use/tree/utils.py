import random
from uiautomation import Control

def random_point_within_bounding_box(node: Control, scale_factor: float = 1.0) -> tuple[int, int]:
    """
    Generate a point within a bounding box, preferring the center for better accuracy.

    Args:
        node (Control): The node with a bounding rectangle
        scale_factor (float, optional): The factor to scale down the bounding box. Defaults to 1.0.

    Returns:
        tuple: A point (x, y) within the bounding box, preferring center for small elements
    """
    box = node.BoundingRectangle
    
    # For very small elements (like search bars), use the exact center
    if box.width() < 50 or box.height() < 20:
        return (box.xcenter(), box.ycenter())
    
    # For medium-sized elements, use a smaller random area around the center
    if box.width() < 200 or box.height() < 50:
        center_x, center_y = box.xcenter(), box.ycenter()
        # Use a small random offset around center (±10 pixels)
        x = center_x + random.randint(-10, 10)
        y = center_y + random.randint(-5, 5)
        # Ensure we stay within bounds
        x = max(box.left, min(box.right, x))
        y = max(box.top, min(box.bottom, y))
        return (x, y)
    
    # For larger elements, use the original scaled approach
    scaled_width = int(box.width() * scale_factor)
    scaled_height = int(box.height() * scale_factor)
    scaled_left = box.left + (box.width() - scaled_width) // 2
    scaled_top = box.top + (box.height() - scaled_height) // 2
    x = random.randint(scaled_left, scaled_left + scaled_width)
    y = random.randint(scaled_top, scaled_top + scaled_height)
    return (x, y)