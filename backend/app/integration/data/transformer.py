import json
from typing import Dict, Any, Callable


class TransformationEngine:
    """Converts internal models to external formats (JSON, XML, CSV stubs)."""

    @classmethod
    def apply_mapping(cls, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Maps fields according to a dictionary.
        Example mapping: {"claim_id": "externalReference", "amount": "totalAmount"}
        """
        result = {}
        for internal_key, value in data.items():
            external_key = mapping.get(internal_key, internal_key)
            result[external_key] = value
        return result

    @classmethod
    def transform_type(cls, data: Dict[str, Any], field: str, func: Callable):
        """Applies a type conversion function to a field."""
        if field in data:
            data[field] = func(data[field])
        return data

    @classmethod
    def to_json(cls, data: Dict[str, Any]) -> str:
        return json.dumps(data)

    @classmethod
    def to_xml_stub(cls, data: Dict[str, Any], root: str = "Root") -> str:
        """Simplified XML stub for demonstration."""
        xml = f"<{root}>"
        for k, v in data.items():
            xml += f"<{k}>{v}</{k}>"
        xml += f"</{root}>"
        return xml

    @classmethod
    def to_csv_stub(cls, data: Dict[str, Any]) -> str:
        """Simplified CSV stub for demonstration."""
        keys = list(data.keys())
        values = [str(data[k]) for k in keys]
        return ",".join(keys) + "\n" + ",".join(values)
