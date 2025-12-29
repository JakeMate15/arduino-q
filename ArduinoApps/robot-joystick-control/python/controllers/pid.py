"""
PID Controller - follows the right wall at a constant distance.
Uses a PID control loop to maintain setpoint distance from the right sensor.
"""
import time
from typing import Tuple
from .base import BaseController


class PIDController(BaseController):
    """PID controller for wall following (right wall)."""
    
    name: str = "pid"
    
    def __init__(
        self,
        setpoint: float = 15.0,
        kp: float = 2.0,
        ki: float = 0.1,
        kd: float = 0.5,
        base_speed: int = 100,
        max_pwm: int = 255
    ):
        """
        Initialize PID controller.
        
        Args:
            setpoint: Target distance from right wall in cm
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            base_speed: Base forward speed (PWM value)
            max_pwm: Maximum PWM value for motors
        """
        self.setpoint = setpoint
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.base_speed = base_speed
        self.max_pwm = max_pwm
        
        # PID state
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = None
        
        # Anti-windup limits for integral term
        self.integral_max = 100.0
        
        # Minimum front distance for obstacle avoidance
        self.min_front_distance = 15.0
    
    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """
        Compute motor PWM values using PID control.
        
        The robot tries to maintain setpoint distance from the right wall.
        If an obstacle is detected in front, it will slow down or stop.
        
        Args:
            dist_frontal: Distance from front sensor in cm
            dist_derecho: Distance from right sensor in cm
            
        Returns:
            Tuple of (pwm_izq, pwm_der) values
        """
        current_time = time.time()
        
        # Calculate dt for proper integral/derivative
        if self.last_time is None:
            dt = 0.02  # Default to 50Hz (20ms)
        else:
            dt = current_time - self.last_time
            dt = max(dt, 0.001)  # Prevent division by zero
        
        self.last_time = current_time
        
        # Handle invalid sensor readings
        if dist_derecho < 0:
            dist_derecho = self.setpoint  # Assume at setpoint if invalid
        if dist_frontal < 0:
            dist_frontal = 100  # Assume clear if invalid
        
        # PID error calculation (positive error = too far from wall)
        error = dist_derecho - self.setpoint
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term with anti-windup
        self.integral += error * dt
        self.integral = max(-self.integral_max, min(self.integral_max, self.integral))
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.last_error) / dt
        d_term = self.kd * derivative
        self.last_error = error
        
        # Total correction
        correction = p_term + i_term + d_term
        
        # Base speed adjustment for front obstacle
        effective_speed = self.base_speed
        if dist_frontal < self.min_front_distance:
            # Slow down as we approach obstacle
            speed_factor = dist_frontal / self.min_front_distance
            effective_speed = int(self.base_speed * speed_factor)
            
            # If very close, stop
            if dist_frontal < 5:
                effective_speed = 0
        
        # Apply correction to differential drive
        # Positive correction = too far from wall = turn right (more power to left motor)
        pwm_izq = effective_speed + int(correction)
        pwm_der = effective_speed - int(correction)
        
        # Clamp to valid PWM range
        pwm_izq = max(-self.max_pwm, min(self.max_pwm, pwm_izq))
        pwm_der = max(-self.max_pwm, min(self.max_pwm, pwm_der))
        
        return pwm_izq, pwm_der
    
    def set_parameters(
        self,
        setpoint: float = None,
        kp: float = None,
        ki: float = None,
        kd: float = None,
        base_speed: int = None
    ) -> None:
        """
        Update PID parameters dynamically.
        
        Args:
            setpoint: New target distance (cm)
            kp: New proportional gain
            ki: New integral gain
            kd: New derivative gain
            base_speed: New base speed
        """
        if setpoint is not None:
            self.setpoint = setpoint
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd
        if base_speed is not None:
            self.base_speed = base_speed
    
    def get_parameters(self) -> dict:
        """Return current PID parameters."""
        return {
            "setpoint": self.setpoint,
            "kp": self.kp,
            "ki": self.ki,
            "kd": self.kd,
            "base_speed": self.base_speed
        }
    
    def on_activate(self) -> None:
        """Reset state when PID mode is activated."""
        self.reset()
    
    def on_deactivate(self) -> None:
        """Reset state when PID mode is deactivated."""
        self.reset()
    
    def reset(self) -> None:
        """Reset PID state (integral, derivative, time)."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = None

