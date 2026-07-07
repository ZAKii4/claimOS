from typing import List, Dict
from app.learning.models import LearningSample


class DatasetBuilder:
    def segment_by_task(self, samples: List[LearningSample]) -> Dict[str, List[LearningSample]]:
        """
        Segments a raw stream of LearningSamples into specialized datasets
        ready for export.
        """
        datasets = {
            "OCR": [],
            "CLASSIFICATION": [],
            "EXTRACTION": [],
            "LAYOUT": [],
            "DECISION": []
        }
        
        for sample in samples:
            if sample.task_type in datasets:
                datasets[sample.task_type].append(sample)
            else:
                # Fallback or mapping
                pass
                
        return {k: v for k, v in datasets.items() if len(v) > 0}
