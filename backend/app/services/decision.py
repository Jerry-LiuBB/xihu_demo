from typing import Any


class DecisionService:
    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self.confidence_threshold = confidence_threshold

    def make_person_decision(self, yolo_response: dict[str, Any], ratio_threshold: float) -> bool:
        image_width = float(yolo_response.get("image_width", 0))
        image_height = float(yolo_response.get("image_height", 0))
        frame_area = image_width * image_height
        if frame_area <= 0:
            return False

        person_ratios: list[float] = []
        for det in yolo_response.get("detections", []):
            if det.get("class_name") != "person":
                continue
            if float(det.get("confidence", 0.0)) < self.confidence_threshold:
                continue
            bbox = det.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = [float(v) for v in bbox]
            box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            person_ratios.append(box_area / frame_area)

        if not person_ratios:
            return False

        return max(person_ratios) >= ratio_threshold
