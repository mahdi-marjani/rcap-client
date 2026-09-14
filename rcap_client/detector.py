from .api import get_models, detect_cells
import random

class Detector:

    def __init__(self):
        self.available_models = get_models()

    def is_model_available(self, target_text: str):
        target_text = target_text.lower()
        return any(
            model in target_text
            for model in self.available_models
        )

    def detect(self, image_array, grid, target_text):
        answers = detect_cells(
            image_array,
            grid,
            target_text,
        )

        random.shuffle(answers)

        return answers