"""
PID Autotune Controller - uses the Relay Method (Åström-Hägglund).
Determines Kp, Ki, and Kd by inducing controlled oscillations.
"""
import time
import numpy as np
from typing import Tuple, List, Optional
from .base import BaseController


class AutotuneController(BaseController):
    """Autotune controller using the Relay Method."""
    
    name: str = "autotune"
    
    def __init__(
        self,
        setpoint: float = 15.0,
        control_step: int = 40,
        base_speed: int = 100,
        cycles_required: int = 8,
        max_pwm: int = 255
    ):
        """
        Initialize Autotune controller.
        
        Args:
            setpoint: Target distance from right wall in cm
            control_step: PWM offset for relay (amplitude of oscillation induction)
            base_speed: Base forward speed
            cycles_required: Number of oscillations to measure
            max_pwm: Maximum PWM value
        """
        self.setpoint = setpoint
        self.control_step = control_step
        self.base_speed = base_speed
        self.cycles_required = cycles_required
        self.max_pwm = max_pwm
        
        # State
        self.active = False
        self.peaks: List[float] = []
        self.cross_times: List[float] = []
        self.last_dist = 0.0
        self.peak_val = 0.0
        self.going_up = False
        self.start_time = 0.0
        
        # Results
        self.kp = 0.0
        self.ki = 0.0
        self.kd = 0.0
        self.finished = False
        
        # Progress (0.0 to 1.0)
        self.progress = 0.0

    def on_activate(self) -> None:
        """Reset state when autotune starts."""
        self.active = True
        self.peaks = []
        self.cross_times = []
        self.last_dist = 0.0
        self.peak_val = 0.0
        self.going_up = False
        self.start_time = time.time()
        self.finished = False
        self.progress = 0.0

    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """
        Apply relay logic and measure oscillations.
        
        Args:
            dist_frontal: Distance from front sensor
            dist_derecho: Distance from right sensor
            
        Returns:
            Tuple of (pwm_izq, pwm_der)
        """
        if self.finished:
            return 0, 0
            
        # Relay Logic (On/Off control)
        # If too far (> setpoint), turn right (toward wall)
        # If too close (< setpoint), turn left (away from wall)
        if dist_derecho > self.setpoint:
            output = self.control_step
        else:
            output = -self.control_step
            
        # Detect Setpoint Crossing
        if (self.last_dist > self.setpoint and dist_derecho <= self.setpoint) or \
           (self.last_dist < self.setpoint and dist_derecho >= self.setpoint):
            
            curr_time = time.time()
            self.cross_times.append(curr_time)
            
            # Store the peak from the previous half-cycle
            if len(self.cross_times) > 1:
                self.peaks.append(abs(self.peak_val - self.setpoint))
                self.peak_val = dist_derecho # Reset for next half-cycle
                
            # Update progress
            self.progress = min(1.0, len(self.peaks) / (self.cycles_required * 2))
            
            # Check if we have enough data
            if len(self.peaks) >= self.cycles_required * 2:
                self._calculate_params()
                self.finished = True
                return 0, 0

        # Track peak value between crossings
        if dist_derecho > self.setpoint:
            if dist_derecho > self.peak_val:
                self.peak_val = dist_derecho
        else:
            if dist_derecho < self.peak_val:
                self.peak_val = dist_derecho
                
        self.last_dist = dist_derecho
        
        # Apply output differentially
        pwm_izq = self.base_speed + output
        pwm_der = self.base_speed - output
        
        # Safety: Stop if obstacle in front
        if dist_frontal < 15:
            pwm_izq, pwm_der = 0, 0
            
        return int(pwm_izq), int(pwm_der)

    def _calculate_params(self) -> None:
        """Calculate PID parameters using Ziegler-Nichols relay method formulas."""
        if not self.peaks or not self.cross_times:
            return
            
        # 1. Calculate Average Amplitud (a)
        # Use only the last few stable oscillations
        recent_peaks = self.peaks[-self.cycles_required:]
        a = np.mean(recent_peaks)
        
        # 2. Calculate Average Period (Tu)
        # Time between every second crossing (full oscillation)
        intervals = []
        for i in range(len(self.cross_times) - 2):
            intervals.append(self.cross_times[i+2] - self.cross_times[i])
        
        Tu = np.mean(intervals)
        
        # 3. Calculate Ultimate Gain (Ku)
        # Ku = (4 * d) / (pi * a) where d is control_step
        d = self.control_step
        Ku = (4.0 * d) / (np.pi * a)
        
        # 4. Ziegler-Nichols PID Formulas
        # These are standard values, but can be tweaked for robot stability
        self.kp = 0.6 * Ku
        self.ki = 1.2 * Ku / Tu
        self.kd = 3.0 * Ku * Tu / 40.0 # Adjusted for stability in high-freq mobile robots
        
        # Apply some sanity limits
        self.kp = np.clip(self.kp, 0.1, 10.0)
        self.ki = np.clip(self.ki, 0.0, 2.0)
        self.kd = np.clip(self.kd, 0.0, 5.0)

    def get_results(self) -> dict:
        """Return the calculated PID parameters."""
        return {
            "kp": round(float(self.kp), 3),
            "ki": round(float(self.ki), 3),
            "kd": round(float(self.kd), 3),
            "finished": self.finished,
            "progress": round(self.progress, 2)
        }
    
    def reset(self) -> None:
        """Reset state."""
        self.on_activate()

