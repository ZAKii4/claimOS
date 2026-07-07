import json
import csv
from typing import List, Optional
from pathlib import Path
from app.learning.models import LearningSample


class ExportEngine:
    def __init__(self, output_dir: str = "/tmp/claimos/datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_jsonl(self, dataset_id: str, samples: List[LearningSample]) -> str:
        filepath = self.output_dir / f"{dataset_id}.jsonl"
        with open(filepath, 'w', encoding='utf-8') as f:
            for sample in samples:
                # Convert datetime to string for json serialization
                dump = sample.model_dump(mode='json')
                f.write(json.dumps(dump) + '\n')
        return str(filepath)

    def export_csv(self, dataset_id: str, samples: List[LearningSample]) -> Optional[str]:
        if not samples:
            return None
            
        filepath = self.output_dir / f"{dataset_id}.csv"
        # Flatten dict for CSV
        headers = ["id", "claim_id", "task_type", "input_data", "expected_output", "corrected_output", "confidence", "operator"]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for sample in samples:
                writer.writerow({
                    "id": sample.id,
                    "claim_id": sample.claim_id,
                    "task_type": sample.task_type,
                    "input_data": json.dumps(sample.input_data),
                    "expected_output": json.dumps(sample.expected_output),
                    "corrected_output": json.dumps(sample.corrected_output),
                    "confidence": sample.confidence,
                    "operator": sample.operator
                })
        return str(filepath)
