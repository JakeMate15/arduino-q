"""
Recorder utility - handles CSV data recording for training.
Records sensor data and motor commands for later model training.
"""
import csv
import os
from datetime import datetime
from typing import Optional


class Recorder:
    """Records robot telemetry data to CSV for training."""
    
    def __init__(self, data_dir: str = None, filename: str = "recorrido_robot.csv"):
        """
        Initialize recorder.
        
        Args:
            data_dir: Directory to save CSV files
            filename: Name of the CSV file
        """
        # Determine data directory
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
        
        self.data_dir = data_dir
        self.filepath = os.path.join(data_dir, filename)
        self.recording = False
        self.min_pwm_threshold = 5  # Only record when robot is moving
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize CSV if it doesn't exist
        self._init_csv()
    
    def _init_csv(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'dist_frontal', 'dist_derecho', 'pwm_izq', 'pwm_der'])
            except Exception:
                pass
    
    def start(self) -> None:
        """Start recording."""
        self.recording = True
    
    def stop(self) -> None:
        """Stop recording."""
        self.recording = False
    
    def toggle(self, active: Optional[bool] = None) -> bool:
        """
        Toggle recording state.
        
        Args:
            active: If provided, set recording to this value. Otherwise toggle.
            
        Returns:
            New recording state
        """
        if active is not None:
            self.recording = active
        else:
            self.recording = not self.recording
        return self.recording
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording
    
    def record(
        self,
        dist_frontal: float,
        dist_derecho: float,
        pwm_izq: int,
        pwm_der: int
    ) -> bool:
        """
        Record a data point if recording is active and robot is moving.
        
        Args:
            dist_frontal: Front sensor distance (cm)
            dist_derecho: Right sensor distance (cm)
            pwm_izq: Left motor PWM value
            pwm_der: Right motor PWM value
            
        Returns:
            True if data was recorded, False otherwise
        """
        if not self.recording:
            return False
        
        # Only record when robot is actually moving
        if abs(pwm_izq) <= self.min_pwm_threshold and abs(pwm_der) <= self.min_pwm_threshold:
            return False
        
        try:
            with open(self.filepath, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    round(dist_frontal, 2),
                    round(dist_derecho, 2),
                    pwm_izq,
                    pwm_der
                ])
            return True
        except Exception:
            return False
    
    def get_filepath(self) -> str:
        """Return the path to the CSV file."""
        return self.filepath
    
    def get_record_count(self) -> int:
        """Return the number of records in the CSV file."""
        try:
            with open(self.filepath, 'r') as f:
                return sum(1 for _ in f) - 1  # Subtract header
        except Exception:
            return 0
    
    def clear(self) -> bool:
        """
        Clear all recorded data (reinitialize CSV with headers only).
        
        Returns:
            True if successful
        """
        try:
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'dist_frontal', 'dist_derecho', 'pwm_izq', 'pwm_der'])
            return True
        except Exception:
            return False

