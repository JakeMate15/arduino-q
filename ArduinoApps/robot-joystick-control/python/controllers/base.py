"""
Clase base para controladores del robot
"""
from abc import ABC, abstractmethod
from typing import Tuple


class BaseController(ABC):
    """Clase abstracta base para todos los controladores"""

    name: str = "base"

    @abstractmethod
    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """Calcula valores PWM de los motores basado en sensores"""
        raise NotImplementedError

    def on_activate(self) -> None:
        """Se llama cuando este controlador se activa"""
        pass

    def on_deactivate(self) -> None:
        """Se llama cuando este controlador se desactiva"""
        pass

    def reset(self) -> None:
        """Reinicia el estado del controlador"""
        pass

