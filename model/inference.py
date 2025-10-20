from ultralytics import YOLO
import os
from helper.resource_path import resource_path

class CalendarDetector:
    def __init__(self):
        model_path = resource_path("model\\yolov8_calendar.pt")
        self.model = YOLO(model_path)

    def detect(self, source_dir, output_dir):
        results = self.model.predict(
            source=source_dir,
            conf=0.4,
            save_txt=True,
            save=False,
            project=output_dir,
            name="calendar_detect"
        )
        return results
