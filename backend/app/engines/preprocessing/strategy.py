"""
Strategy Builder for Adaptive Preprocessing.
"""

from app.engines.iqa.models import ImageQualityReport
from app.engines.preprocessing.operations.base import BaseOperation
from app.engines.preprocessing.operations.binarization import AdaptiveThresholdOperation, SauvolaBinarization
from app.engines.preprocessing.operations.exposure import CLAHEOperation, ShadowRemovalOperation
from app.engines.preprocessing.operations.filters import MedianBlurDenoise, MorphologicalOpening, NonLocalMeansDenoise, SharpeningOperation
from app.engines.preprocessing.operations.geometry import DeskewOperation, RotateOperation


class StrategyBuilder:
    """
    Constructs a dynamic sequence of preprocessing operations based on IQA metrics.
    """
    
    def build_strategy(self, iqa_report: ImageQualityReport) -> list[BaseOperation]:
        operations: list[BaseOperation] = []
        
        # 1. Geometry Corrections (First because they change coordinates)
        if iqa_report.rotation != 0:
            operations.append(RotateOperation(iqa_report.rotation))
            
        if abs(iqa_report.deskew_angle) > 0.5:
            operations.append(DeskewOperation(iqa_report.deskew_angle))
            
        # 2. Noise Reduction
        if iqa_report.noise_level > 0.15:
            operations.append(NonLocalMeansDenoise())
        elif iqa_report.noise_level > 0.05:
            operations.append(MedianBlurDenoise(kernel_size=3))
            
        # 3. Blur Correction
        # If blurry, sharpen it (Unsharp Mask)
        if iqa_report.is_blurred:
            operations.append(SharpeningOperation())
            
        # 4. Exposure & Shadow Correction
        if iqa_report.has_shadows:
            # We use shadow removal (division) to normalize background
            operations.append(ShadowRemovalOperation())
            
        if iqa_report.contrast < 40.0: # Arbitrary heuristic threshold
            operations.append(CLAHEOperation(clip_limit=2.0))
            
        # 5. Binarization (Final step for OCR)
        # We always binarize to guarantee pure black and white for OCR engines.
        # Sauvola is expensive but excellent for shadows or degraded contrast.
        if iqa_report.has_shadows or iqa_report.noise_level > 0.1:
            operations.append(SauvolaBinarization(window_size=25, k=0.2))
        else:
            operations.append(AdaptiveThresholdOperation(block_size=15, c=10))
            
        # 6. Post-binarization cleanup
        if iqa_report.noise_level > 0.1:
            # Clean up tiny speckles
            operations.append(MorphologicalOpening(kernel_size=2))
            
        return operations
