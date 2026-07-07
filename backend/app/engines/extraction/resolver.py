from collections import defaultdict
from app.engines.extraction.models import ExtractedEntity

class EntityResolver:
    """
    Resolves conflicts when multiple extractors return the same entity field.
    """

    def resolve(self, entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
        """
        Groups entities by field_name and picks the best candidate per field.
        """
        field_groups = defaultdict(list)
        for entity in entities:
            field_groups[entity.field_name].append(entity)

        resolved = []
        for field_name, candidates in field_groups.items():
            if not candidates:
                continue
            if len(candidates) == 1:
                resolved.append(candidates[0])
            else:
                # Conflict resolution logic: Highest confidence wins.
                # In more advanced versions, this could check for consensus
                # or layout precedence (Form fields > Free text).
                best_candidate = max(candidates, key=lambda e: e.confidence)
                resolved.append(best_candidate)
                
        return resolved
