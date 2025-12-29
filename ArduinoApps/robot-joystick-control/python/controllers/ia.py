"""
IA Controller - uses trained XGBoost model for autonomous navigation.
Loads pre-trained model and scaler from data/ directory.
"""
import os
from typing import Tuple, Optional
import numpy as np
from .base import BaseController


class IAController(BaseController):
    """AI-based controller using XGBoost model."""
    
    name: str = "ia"
    
    def __init__(self, data_dir: str = None, max_pwm: int = 255):
        """
        Initialize IA controller.
        
        Args:
            data_dir: Directory containing model files (cerebro_robot.pkl, escalador.pkl)
            max_pwm: Maximum PWM value for motors
        """
        self.max_pwm = max_pwm
        self.modelo = None
        self.escalador = None
        self.available = False
        
        # Determine data directory
        if data_dir is None:
            # Default to data/ folder relative to this file's parent
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
        
        self.data_dir = data_dir
        self.model_path = os.path.join(data_dir, 'cerebro_robot.pkl')
        self.scaler_path = os.path.join(data_dir, 'escalador.pkl')
        
        # Try to load model
        self._load_model()
    
    def _load_model(self) -> bool:
        """
        Attempt to load the trained model and scaler.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            import joblib
            
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.modelo = joblib.load(self.model_path)
                self.escalador = joblib.load(self.scaler_path)
                self.available = True
                return True
            else:
                self.available = False
                return False
                
        except ImportError:
            self.available = False
            return False
        except Exception:
            self.available = False
            return False
    
    def is_available(self) -> bool:
        """Check if the IA model is loaded and ready."""
        return self.available and self.modelo is not None and self.escalador is not None
    
    def compute(self, dist_frontal: float, dist_derecho: float) -> Tuple[int, int]:
        """
        Compute motor PWM values using the trained model.
        
        Args:
            dist_frontal: Distance from front sensor in cm
            dist_derecho: Distance from right sensor in cm
            
        Returns:
            Tuple of (pwm_izq, pwm_der) values
        """
        if not self.is_available():
            return 0, 0
        
        try:
            # Prepare input for model
            X_input = np.array([[dist_frontal, dist_derecho]])
            X_scaled = self.escalador.transform(X_input)
            
            # Get prediction
            prediccion = self.modelo.predict(X_scaled)
            vI, vD = prediccion[0]
            
            # Clamp to valid PWM range
            pwm_izq = int(np.clip(vI, -self.max_pwm, self.max_pwm))
            pwm_der = int(np.clip(vD, -self.max_pwm, self.max_pwm))
            
            return pwm_izq, pwm_der
            
        except Exception:
            return 0, 0
    
    def reload_model(self) -> bool:
        """
        Reload the model from disk (useful after retraining).
        
        Returns:
            True if reload successful
        """
        return self._load_model()
    
    def get_model_info(self) -> dict:
        """Return information about the loaded model."""
        return {
            "available": self.available,
            "model_path": self.model_path,
            "scaler_path": self.scaler_path,
            "model_type": type(self.modelo).__name__ if self.modelo else None
        }
    
    def on_activate(self) -> None:
        """Verify model is available when activating."""
        if not self.is_available():
            # Try to reload in case files were added
            self._load_model()
    
    def on_deactivate(self) -> None:
        """Nothing special needed on deactivation."""
        pass
    
    def reset(self) -> None:
        """IA controller has no state to reset."""
        pass

