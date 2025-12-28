from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC

# Initialize WebUI
ui = WebUI()

# Initialize Local Video Detection (uses /dev/video by default)
# This brick handles camera capture, detection, and video streaming automatically.
detection_stream = VideoObjectDetection(confidence=0.5)

# Callback to send detection data to the WebUI
def send_detections_to_ui(detections: dict):
    # Formatear detecciones para que coincidan con lo que espera el HTML
    formatted_detections = []
    for label, details in detections.items():
        formatted_detections.append({
            "class_name": label,
            "confidence": f"{details.get('confidence', 0) * 100:.2f}"
        })
    
    ui.send_message("detection", {
        "detections": formatted_detections, 
        "count": len(formatted_detections)
    })

# Register the callback
detection_stream.on_detect_all(send_detections_to_ui)

# Start the application
if __name__ == "__main__":
    App.run()