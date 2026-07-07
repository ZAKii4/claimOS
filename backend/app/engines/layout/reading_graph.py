from typing import Callable, Optional

from app.engines.layout.models import LayoutPage, LayoutRegion
from app.engines.layout.relationships import (
    are_boxes_close,
    euclidean_distance,
    is_horizontally_aligned,
    is_vertically_aligned,
)


class ReadingGraphBuilder:
    """
    Builds the spatial relationship graph and calculates the correct reading order
    for a layout page containing various regions.
    """

    def __init__(self, page: LayoutPage):
        self.page = page

    def build_spatial_relationships(self):
        """
        Populate parent/children relationships and find nearest neighbors.
        For instance, find form fields that have label-value relations.
        """
        # Assign IDs to regions without them (should already be done by default factory)
        
        # We can implement KD-Trees or R-Trees here in the future for O(N log N).
        # For now, an O(N^2) pairwise approach is sufficient for typical document pages (N < 200).
        regions = self.page.regions
        
        # Example logic: Link form fields based on horizontal alignment
        # (This can also be delegated to the FormDetector, but the graph builder can provide utility methods)
        
    def calculate_reading_order(self):
        """
        Sorts the regions in the page to establish a natural reading order.
        A standard approach for Western languages is top-to-bottom, left-to-right.
        More complex layouts (columns) require hierarchical sorting.
        """
        if not self.page.regions:
            return

        # Simple heuristic: sort by Y primarily, then by X.
        # To handle minor vertical variations, we bucket the Y coordinates.
        y_tolerance = 0.02
        
        def sort_key(region: LayoutRegion):
            # Quantize y-min to bucket
            y_bucket = round(region.bounding_box.y_min / y_tolerance)
            return (y_bucket, region.bounding_box.x_min)

        sorted_regions = sorted(self.page.regions, key=sort_key)
        
        for idx, region in enumerate(sorted_regions):
            region.reading_order = idx
            
        self.page.regions = sorted_regions

    def find_nearest_neighbor(
        self, 
        source_region: LayoutRegion, 
        candidates: list[LayoutRegion], 
        condition: Optional[Callable[[LayoutRegion, LayoutRegion], bool]] = None
    ) -> Optional[LayoutRegion]:
        """Find the closest region among candidates that satisfies an optional condition."""
        best_match = None
        min_dist = float('inf')

        for candidate in candidates:
            if candidate.id == source_region.id:
                continue
                
            if condition and not condition(source_region, candidate):
                continue
                
            dist = euclidean_distance(source_region.bounding_box, candidate.bounding_box)
            if dist < min_dist:
                min_dist = dist
                best_match = candidate
                
        return best_match
