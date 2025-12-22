from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC

IP_COMPUTADORA = "192.168.1.151" 
URL_FLASK = f"http://{IP_COMPUTADORA}:5000/video"

ui = WebUI()

# IMPORTANTE: Pasamos la URL del stream como fuente (source)
# La Uno Q procesará este stream de red usando el hardware de Qualcomm
detection_stream = VideoObjectDetection(
    source=URL_FLASK, 
    confidence=0.5, 
    debounce_sec=0.0
)

ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

def send_detections_to_ui(detections: dict):
    for key, value in detections.items():
        # En el README dice que value es el dict o el float directo, 
        # ajustamos según la estructura del ejemplo
        conf = value.get("confidence") if isinstance(value, dict) else value
        
        entry = {
            "content": key,
            "confidence": conf,
            "timestamp": datetime.now(UTC).isoformat()
        }
        ui.send_message("detection", message=entry)
        
        # Ejemplo: Si detecta una persona en la cámara remota, imprime en consola
        if key == "person":
            print(f"¡Alerta! Alguien está frente a la otra computadora. Confianza: {conf}")

detection_stream.on_detect_all(send_detections_to_ui)

App.run()