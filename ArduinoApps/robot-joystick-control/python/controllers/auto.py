"""
Auto Controller - Object detection based autonomous navigation
"""
from .base import BaseController


class AutoController(BaseController):
    """
    Automatic controller for autonomous navigation using object detection.

    Rules:
    - If objects from list A detected -> move forward
    - If objects from list B detected -> move backward
    - If both A and B detected -> stop
    - If neither A nor B detected -> stop
    - If frontal distance < 20cm -> stop (safety override)
    """

    def __init__(self, list_a=None, list_b=None, base_speed=150, min_distance=20.0):
        super().__init__()

        # Object lists (default values)
        self.list_a = list_a or ["cat", "dog", "person"]  # Forward objects
        self.list_b = list_b or ["cell phone", "cup", "clock"]  # Backward objects

        # Control parameters
        self.base_speed = base_speed  # PWM value for motors
        self.min_distance = min_distance  # Minimum safe distance (cm)

        # Detection state
        self.detected_objects = {}  # {object_name: confidence}
        self.has_list_a = False
        self.has_list_b = False

    def on_activate(self):
        """Called when this controller becomes active."""
        self.detected_objects = {}
        self.has_list_a = False
        self.has_list_b = False

    def on_deactivate(self):
        """Called when switching away from this controller."""
        self.detected_objects = {}
        self.has_list_a = False
        self.has_list_b = False

    def update_detections(self, detections: dict):
        """
        Update detected objects from camera.

        Args:
            detections: Dictionary of {object_name: {"confidence": float}}
        """
        self.detected_objects = detections

        # Check which lists have detected objects
        self.has_list_a = any(obj in self.list_a for obj in detections.keys())
        self.has_list_b = any(obj in self.list_b for obj in detections.keys())

    def set_object_lists(self, list_a: list, list_b: list):
        """Update object detection lists."""
        self.list_a = list_a
        self.list_b = list_b

    def get_object_lists(self):
        """Get current object lists."""
        return {"list_a": self.list_a, "list_b": self.list_b}

    def compute(self, d_frontal: float, d_derecho: float) -> tuple:
        """
        Compute motor commands based on sensor readings and object detection.

        Args:
            d_frontal: Distance from front sensor (cm)
            d_derecho: Distance from right sensor (cm)

        Returns:
            Tuple of (pwm_left, pwm_right) in range [-255, 255]
        """
        # Safety override: Stop if too close to obstacle
        if d_frontal > 0 and d_frontal < self.min_distance:
            return 0, 0

        # Decision logic based on detected objects
        if self.has_list_a and self.has_list_b:
            # Both lists detected -> stop
            return 0, 0
        elif self.has_list_a:
            # Only list A -> move forward
            return self.base_speed, self.base_speed
        elif self.has_list_b:
            # Only list B -> move backward
            return -self.base_speed, -self.base_speed
        else:
            # No relevant objects detected -> stop
            return 0, 0
