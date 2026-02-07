from dataclasses import dataclass
from typing import List


@dataclass
class Detection:
    label: str
    confidence: float
    risk_zone: bool
    camera: str


class VisionPipeline:
    def __init__(self, model: str = "yolov8n"):
        self.model = model

    def detect(self, _frame, camera: str) -> List[Detection]:
        # Stub: integrate ONNX/TFLite model here.
        return [Detection(label="clear", confidence=1.0, risk_zone=False, camera=camera)]

    @staticmethod
    def should_stop(detections: List[Detection], threshold: float = 0.45) -> bool:
        for d in detections:
            if d.risk_zone and d.confidence >= threshold and d.label in {"person", "stop_sign", "obstacle"}:
                return True
        return False
