"""
Manual controller - handles joystick and turn button inputs.
This controller does NOT compute based on sensors, it receives direct commands.
"""
from typing import Tuple
from .base import BaseController


class ManualController(BaseController):
    """Manual control via joystick or turn buttons."""
    
    name: str = "manual"
    
    def __init__(self, max_pwm: int = 255):
        self.max_pwm = max_pwm
        self.pwm_izq = 0
        self.pwm_der = 0
        self.vel_giro = 150
    
    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """
        Manual mode doesn't use sensors for control.
        Returns the last set PWM values from joystick/buttons.
        """
        return self.pwm_izq, self.pwm_der
    
    def process_joystick(self, x: int, y: int) -> Tuple[int, int]:
        """
        Process joystick input and calculate motor PWM values.
        
        Args:
            x: Joystick X axis (-255 to 255)
            y: Joystick Y axis (-255 to 255)
            
        Returns:
            Tuple of (pwm_izq, pwm_der)
        """
        def scale(val: int) -> int:
            return int((val / 255.0) * (self.max_pwm / 2.0))
        
        scaled_x = scale(x)
        scaled_y = scale(y)
        
        # Differential drive mixing
        vI = scaled_y + scaled_x
        vD = scaled_y - scaled_x
        
        # Clamp to max PWM
        self.pwm_izq = max(-self.max_pwm, min(self.max_pwm, vI))
        self.pwm_der = max(-self.max_pwm, min(self.max_pwm, vD))
        
        return self.pwm_izq, self.pwm_der
    
    def process_turn(self, direction: str, action: str) -> Tuple[int, int]:
        """
        Process turn button input.
        
        Args:
            direction: 'izq' or 'der'
            action: 'start' or 'stop'
            
        Returns:
            Tuple of (pwm_izq, pwm_der)
        """
        if action == "stop":
            self.pwm_izq, self.pwm_der = 0, 0
        elif direction == "izq":
            self.pwm_izq, self.pwm_der = -self.vel_giro, self.vel_giro
        elif direction == "der":
            self.pwm_izq, self.pwm_der = self.vel_giro, -self.vel_giro
        
        return self.pwm_izq, self.pwm_der
    
    def stop(self) -> Tuple[int, int]:
        """Stop both motors."""
        self.pwm_izq, self.pwm_der = 0, 0
        return self.pwm_izq, self.pwm_der
    
    def on_deactivate(self) -> None:
        """Stop motors when switching away from manual mode."""
        self.stop()
    
    def reset(self) -> None:
        """Reset PWM values to zero."""
        self.pwm_izq = 0
        self.pwm_der = 0

