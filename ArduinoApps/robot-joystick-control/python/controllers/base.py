"""
Base controller class for robot control modes.
All controllers must inherit from this class and implement the compute method.
"""
from abc import ABC, abstractmethod
from typing import Tuple


class BaseController(ABC):
    """Abstract base class for all robot controllers."""
    
    name: str = "base"
    
    @abstractmethod
    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """
        Compute motor PWM values based on sensor readings.
        
        Args:
            dist_frontal: Distance from front sensor in cm
            dist_derecho: Distance from right sensor in cm
            
        Returns:
            Tuple of (pwm_izq, pwm_der) values for left and right motors
        """
        raise NotImplementedError
    
    def on_activate(self) -> None:
        """Called when this controller becomes active."""
        pass
    
    def on_deactivate(self) -> None:
        """Called when this controller is deactivated."""
        pass
    
    def reset(self) -> None:
        """Reset controller state (e.g., integral terms, buffers)."""
        pass

