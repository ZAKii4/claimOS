import cv2
import numpy as np

from app.engines.layout.models import LayoutPage


def draw_layout_visualization(image: np.ndarray, layout_page: LayoutPage) -> np.ndarray:
    """
    Draws bounding boxes and labels for all layout regions.
    Colors are mapped by region type.
    """
    canvas = image.copy()
    h, w = canvas.shape[:2]

    # BGR colors
    COLORS = {
        "paragraph": (0, 255, 0),      # Green
        "header": (255, 255, 0),       # Cyan
        "table": (255, 0, 0),          # Blue
        "signature": (0, 0, 255),      # Red
        "stamp": (128, 0, 128),        # Purple
        "checkbox": (255, 165, 0),     # Orange
        "form_field": (0, 165, 255),   # Orange-ish
        "image": (255, 0, 255)         # Magenta
    }

    for region in layout_page.regions:
        x_min = int(region.bounding_box.x_min * w)
        y_min = int(region.bounding_box.y_min * h)
        x_max = int(region.bounding_box.x_max * w)
        y_max = int(region.bounding_box.y_max * h)

        color = COLORS.get(region.type, (128, 128, 128))
        
        cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max), color, 2)
        
        # Draw label
        label = f"{region.type}"
        if getattr(region, "reading_order", None) is not None:
            label = f"{region.reading_order}:{label}"
            
        cv2.putText(
            canvas, 
            label, 
            (x_min, max(10, y_min - 5)), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            color, 
            1
        )
        
        # Special logic for FormField linking
        if region.type == "form_field" and hasattr(region, "value") and region.value:
            # We don't have bounding box of value directly in this simplified model,
            # but ideally we would draw an arrow from label to value.
            pass

    return canvas
