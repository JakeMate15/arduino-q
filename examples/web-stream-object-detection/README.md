# Object Detection Web Stream

This project demonstrates how to perform object detection on a video stream from a web server (e.g., an IP Webcam) using the Arduino App framework.

## Description

The application connects to a video stream URL (default: `http://192.168.1.94:4747/video`), reads frames, and processes them using the `arduino:object_detection` brick. Detected objects are logged to the console and sent to the Web UI.

## Configuration

The stream URL is configured in `python/main.py`:
```python
STREAM_URL = 'http://192.168.1.94:4747/video'
```

## How to Run

1. Ensure the video stream is available at the configured URL.
2. Run the application using the Arduino App runner.

## Bricks Used

- `arduino:object_detection`: For detecting objects in video frames.
- `arduino:web_ui`: For displaying detection results.
