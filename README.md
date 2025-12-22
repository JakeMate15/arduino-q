# Arduino Q - Bricks Library

This repository contains the official **Bricks** (modular components) provided by Arduino for the Arduino UNO Q platform. These bricks are pre-built, reusable modules that enable rapid development of IoT applications.

## What are Bricks?

Bricks are modular Python components that provide specific functionality for your Arduino UNO Q applications. Each brick encapsulates a feature or service, allowing you to build complex applications by combining multiple bricks together.

## Available Bricks

This repository includes the following official Arduino bricks:

### AI & Machine Learning
- **Image Classification** - Classify images using pre-trained models
- **Object Detection** - Detect objects in images with bounding boxes
- **Audio Classification** - Classify audio sounds and events
- **Keyword Spotting** - Detect specific keywords in audio
- **Visual Anomaly Detection** - Detect visual anomalies in images
- **Vibration Anomaly Detection** - Detect anomalies from sensor data
- **Motion Detection** - Recognize motion patterns from accelerometer

### User Interfaces
- **Web UI (HTML)** - Serve HTML/JavaScript web interfaces
- **Streamlit UI** - Create Python-based web interfaces

### Communication & Storage
- **Arduino Cloud** - Connect to Arduino Cloud IoT platform
- **MQTT** - MQTT communication protocol
- **SQL Database** - SQLite database storage
- **Time Series Database** - InfluxDB time series storage

### Utilities
- **Camera Code Detection** - Scan QR codes and barcodes
- **Weather Forecast** - Get weather data from online APIs
- **Wave Generator** - Generate audio waveforms
- **Mood Detector** - Analyze text sentiment
- **Cloud LLM** - Integrate with cloud-based language models
- **Air Quality Monitoring** - Monitor air quality sensors

## Repository Structure

```
arduino-q/
├── bricks/          # All available bricks (modular components)
│   ├── arduino_cloud/
│   ├── web_ui/
│   ├── object_detection/
│   └── ...
├── examples/        # Complete example applications
│   ├── blink/
│   ├── cloud-blink/
│   └── ...
└── README.md
```

## How to Use

Each brick includes:
- **Configuration file** (`brick_config.yaml`) - Brick metadata and settings
- **Python implementation** - The brick's functionality
- **Documentation** (`README.md`) - Usage instructions
- **Examples** - Code examples showing how to use the brick

### Example Usage

```python
from arduino.app_bricks.arduino_cloud import ArduinoCloud
from arduino.app_utils import App

# Initialize a brick
arduino_cloud = ArduinoCloud()

# Use the brick's functionality
arduino_cloud.register("led", value=False)

# Start the application
App.start_brick(arduino_cloud)
```

## Examples

The `examples/` directory contains complete applications demonstrating how to use these bricks in real projects. Each example includes:
- Python application code
- Arduino sketch (when needed)
- Configuration files
- Documentation

## Documentation

For detailed documentation on each brick, see the individual `README.md` files in each brick's directory, or check the documentation in `bricks/static/docs/`.

## License

These bricks are provided by Arduino SRL and are subject to their respective licenses (typically MPL-2.0).

---

**Note:** These are the official bricks included with the Arduino UNO Q platform. They are maintained and provided by Arduino for use in your projects.
