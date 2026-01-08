"""
Controlador Manual - Maneja entradas del joystick y botones de giro
"""
from typing import Tuple
from .base import BaseController


class ManualController(BaseController):
    """Control manual mediante joystick o botones de giro"""

    name: str = "manual"

    def __init__(self, max_pwm: int = 255):
        self.max_pwm = max_pwm
        self.pwm_izq = 0
        self.pwm_der = 0
        self.vel_giro = 150

    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """El modo manual no usa sensores, retorna los últimos valores PWM"""
        return self.pwm_izq, self.pwm_der

    def process_joystick(self, x: int, y: int) -> Tuple[int, int]:
        """Procesa entrada del joystick y calcula valores PWM"""
        def scale(val: int) -> int:
            return int((val / 255.0) * (self.max_pwm / 2.0))

        scaled_x = scale(x)
        scaled_y = scale(y)

        # Mezcla diferencial para tracción diferencial
        vI = scaled_y + scaled_x
        vD = scaled_y - scaled_x

        # Limitar a PWM máximo
        self.pwm_izq = max(-self.max_pwm, min(self.max_pwm, vI))
        self.pwm_der = max(-self.max_pwm, min(self.max_pwm, vD))

        return self.pwm_izq, self.pwm_der

    def process_turn(self, direction: str, action: str) -> Tuple[int, int]:
        """Procesa entrada de botones de giro"""
        if action == "stop":
            self.pwm_izq, self.pwm_der = 0, 0
        elif direction == "izq":
            self.pwm_izq, self.pwm_der = -self.vel_giro, self.vel_giro
        elif direction == "der":
            self.pwm_izq, self.pwm_der = self.vel_giro, -self.vel_giro

        return self.pwm_izq, self.pwm_der

    def stop(self) -> Tuple[int, int]:
        """Detiene ambos motores"""
        self.pwm_izq, self.pwm_der = 0, 0
        return self.pwm_izq, self.pwm_der

    def on_deactivate(self) -> None:
        """Detiene motores al cambiar de modo"""
        self.stop()

    def reset(self) -> None:
        """Reinicia valores PWM a cero"""
        self.pwm_izq = 0
        self.pwm_der = 0

