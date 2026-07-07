"""
Lookup tables endpoint — generic read access to all reference tables.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import lookups as lookup_models
from app.schemas.common import LabelledLookupSchema, LookupSchema

router = APIRouter(prefix="/lookups", tags=["Lookups"])

# Map URL path names to model classes.
# Tables with labels use LabelledLookupSchema; others use LookupSchema.
_LOOKUP_REGISTRY: dict[str, tuple[type, type]] = {
    "claim-types": (lookup_models.ClaimType, LabelledLookupSchema),
    "claim-statuses": (lookup_models.ClaimStatus, LookupSchema),
    "document-types": (lookup_models.DocumentType, LabelledLookupSchema),
    "party-roles": (lookup_models.PartyRole, LookupSchema),
    "extraction-methods": (lookup_models.ExtractionMethod, LookupSchema),
    "event-types": (lookup_models.EventType, LookupSchema),
    "flag-reasons": (lookup_models.FlagReason, LookupSchema),
    "discrepancy-types": (lookup_models.DiscrepancyType, LookupSchema),
    "damage-zones": (lookup_models.DamageZone, LookupSchema),
    "damage-severities": (lookup_models.DamageSeverity, LookupSchema),
    "body-regions": (lookup_models.BodyRegion, LookupSchema),
    "injury-types": (lookup_models.InjuryType, LookupSchema),
    "prognoses": (lookup_models.Prognosis, LookupSchema),
    "weather-conditions": (lookup_models.WeatherCondition, LookupSchema),
    "road-conditions": (lookup_models.RoadCondition, LookupSchema),
    "operator-roles": (lookup_models.OperatorRole, LookupSchema),
    "product-types": (lookup_models.ProductType, LabelledLookupSchema),
}


@router.get(
    "/{table_name}",
    summary="List Lookup Values",
    description="Return all values from a reference table. Use the table name in kebab-case.",
)
def list_lookup_values(
    table_name: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    entry = _LOOKUP_REGISTRY.get(table_name)
    if entry is None:
        available = ", ".join(sorted(_LOOKUP_REGISTRY.keys()))
        raise HTTPException(
            status_code=404,
            detail=f"Unknown lookup table '{table_name}'. Available: {available}",
        )

    model_class, schema_class = entry
    stmt = select(model_class)
    rows = db.scalars(stmt).all()
    return [schema_class.model_validate(row).model_dump() for row in rows]
