"""
Controlador Automático - Navegación autónoma basada en detección de objetos
"""
from .base import BaseController


class AutoController(BaseController):
    """
    Controlador automático para navegación usando detección de objetos

    Reglas:
    - Lista A detectada -> adelante
    - Lista B detectada -> atrás
    - Ambas listas o ninguna -> detener
    - Distancia frontal < min_distance -> detener (seguridad)
    """

    def __init__(self, list_a=None, list_b=None, base_speed=150, min_distance=20.0):
        super().__init__()

        self.list_a = list_a or ["cat", "dog", "person"]
        self.list_b = list_b or ["cell phone", "cup", "clock"]
        self.base_speed = base_speed
        self.min_distance = min_distance

        self.detected_objects = {}
        self.has_list_a = False
        self.has_list_b = False

    def on_activate(self):
        """Se llama cuando este controlador se activa"""
        self.detected_objects = {}
        self.has_list_a = False
        self.has_list_b = False

    def on_deactivate(self):
        """Se llama al cambiar de controlador"""
        self.detected_objects = {}
        self.has_list_a = False
        self.has_list_b = False

    def update_detections(self, detections: dict):
        """Actualiza objetos detectados desde la cámara"""
        self.detected_objects = detections
        self.has_list_a = any(obj in self.list_a for obj in detections.keys())
        self.has_list_b = any(obj in self.list_b for obj in detections.keys())

    def set_object_lists(self, list_a: list, list_b: list):
        """Actualiza listas de objetos"""
        self.list_a = list_a
        self.list_b = list_b

    def get_object_lists(self):
        """Retorna listas de objetos actuales"""
        return {"list_a": self.list_a, "list_b": self.list_b}

    def compute(self, d_frontal: float, d_derecho: float) -> tuple:
        """Calcula comandos de motores basado en sensores y detecciones"""
        # Seguridad: detener si está muy cerca de obstáculo
        if d_frontal > 0 and d_frontal < self.min_distance:
            return 0, 0

        # Lógica de decisión basada en objetos detectados
        if self.has_list_a and self.has_list_b:
            return 0, 0
        elif self.has_list_a:
            return self.base_speed, self.base_speed
        elif self.has_list_b:
            return -self.base_speed, -self.base_speed
        else:
            return 0, 0
