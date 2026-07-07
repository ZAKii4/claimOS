from typing import Any

from app.engines.ocr.models import BoundingBox


def compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Computes the Intersection over Union (IoU) of two bounding boxes."""
    # Determine coordinates of intersection rectangle
    x_left = max(box1.x_min, box2.x_min)
    y_top = max(box1.y_min, box2.y_min)
    x_right = min(box1.x_max, box2.x_max)
    y_bottom = min(box1.y_max, box2.y_max)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    iou = intersection_area / float(box1.area + box2.area - intersection_area)
    return iou


def is_horizontally_aligned(box1: BoundingBox, box2: BoundingBox, tolerance: float = 0.02) -> bool:
    """Checks if two boxes are on the same horizontal line, given a tolerance."""
    # Check vertical overlap or y-center proximity
    center_y1 = (box1.y_min + box1.y_max) / 2
    center_y2 = (box2.y_min + box2.y_max) / 2
    return abs(center_y1 - center_y2) <= tolerance


def is_vertically_aligned(box1: BoundingBox, box2: BoundingBox, tolerance: float = 0.02) -> bool:
    """Checks if two boxes are in the same vertical column, given a tolerance."""
    center_x1 = (box1.x_min + box1.x_max) / 2
    center_x2 = (box2.x_min + box2.x_max) / 2
    return abs(center_x1 - center_x2) <= tolerance


def euclidean_distance(box1: BoundingBox, box2: BoundingBox) -> float:
    """Distance between the centers of two boxes."""
    cx1 = (box1.x_min + box1.x_max) / 2
    cy1 = (box1.y_min + box1.y_max) / 2
    cx2 = (box2.x_min + box2.x_max) / 2
    cy2 = (box2.y_min + box2.y_max) / 2
    return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5


def are_boxes_close(box1: BoundingBox, box2: BoundingBox, max_dist_x: float = 0.1, max_dist_y: float = 0.05) -> bool:
    """Check if two boxes are close enough to be considered neighbors."""
    dist_x = max(0, max(box1.x_min, box2.x_min) - min(box1.x_max, box2.x_max))
    dist_y = max(0, max(box1.y_min, box2.y_min) - min(box1.y_max, box2.y_max))
    return dist_x <= max_dist_x and dist_y <= max_dist_y
