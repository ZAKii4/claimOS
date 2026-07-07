import json
from typing import Dict, Any


class ReportEngine:
    """Generates scheduled or ad-hoc reports in various formats."""

    @classmethod
    def generate_report(cls, tenant_id: str, report_type: str, format_str: str) -> str:
        """Returns the content of a generated report."""
        
        # Stub data based on report type
        data = {"tenant": tenant_id, "type": report_type, "status": "Generated"}
        
        if report_type == "operational":
            data["processed_claims"] = 150
            data["pending_claims"] = 25
            
        if format_str.upper() == "JSON":
            return json.dumps(data)
        elif format_str.upper() == "CSV":
            keys = list(data.keys())
            vals = [str(v) for v in data.values()]
            return ",".join(keys) + "\n" + ",".join(vals)
        elif format_str.upper() == "MARKDOWN":
            md = f"# {report_type.capitalize()} Report\n\n"
            for k, v in data.items():
                md += f"- **{k}**: {v}\n"
            return md
        else:
            return f"Format {format_str} not supported."
