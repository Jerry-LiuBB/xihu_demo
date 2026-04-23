import unittest

from backend.app.services.decision import DecisionService


class DecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = DecisionService(confidence_threshold=0.5)

    def test_true_when_ratio_meets_threshold(self):
        payload = {
            "image_width": 100,
            "image_height": 100,
            "detections": [
                {"class_name": "person", "confidence": 0.8, "bbox": [0, 0, 60, 60]},
            ],
        }
        self.assertTrue(self.svc.make_person_decision(payload, ratio_threshold=0.35))

    def test_false_when_no_person(self):
        payload = {
            "image_width": 100,
            "image_height": 100,
            "detections": [
                {"class_name": "cat", "confidence": 0.9, "bbox": [0, 0, 90, 90]},
            ],
        }
        self.assertFalse(self.svc.make_person_decision(payload, ratio_threshold=0.1))


if __name__ == "__main__":
    unittest.main()
