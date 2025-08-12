# Saba - Audio Visualization Application

A beautiful 3D audio visualization application built with PyQt5 and OpenGL.

## Project Structure

The application has been modularized into separate components:

```
Saba/
├── UI/
│   ├── __init__.py
│   ├── app.py              # Main application entry point (legacy)
│   ├── main.py             # Main application entry point (new)
│   ├── models.py           # 3D sphere model and geometry
│   ├── audio_analyzer.py   # Audio processing and analysis
│   ├── saba_gl.py          # OpenGL rendering widget
│   └── saba_window.py      # Main application window
├── services/
│   ├── __init__.py
│   └── speech_service.py   # Speech synthesis service
├── config/
│   └── __init__.py
├── run_saba.py             # Application launcher
├── main.py                 # Speech service entry point
├── output.wav              # Audio file for visualization
└── requirements.txt
```

## Components

### UI Components
- **`models.py`**: Contains the `SphereModel` class that generates the 3D sphere geometry
- **`audio_analyzer.py`**: Contains the `AudioAnalyzer` class for audio playback and FFT analysis
- **`saba_gl.py`**: Contains the `SabaGL` OpenGL widget with all rendering logic
- **`saba_window.py`**: Contains the `SabaWindow` class for the main application window
- **`main.py`**: Main application entry point that runs the UI

### Services
- **`speech_service.py`**: Speech synthesis and recognition services

## Running the Application

### Option 1: Using the launcher script (Recommended)
```bash
python run_saba.py
```

### Option 2: Running from the UI directory
```bash
cd UI
python main.py
```

### Option 3: Running the legacy app.py
```bash
cd UI
python app.py
```

## Features

- **3D Audio Visualization**: Real-time 3D sphere visualization that responds to audio
- **Audio Analysis**: FFT-based spectrum analysis with RMS metering
- **Beautiful UI**: Modern HUD-style interface with dashboard
- **Modular Design**: Clean separation of concerns with reusable components
- **Persistent Application**: Application runs until manually closed

## Dependencies

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Audio File

The application expects an `output.wav` file in the root directory. If the file doesn't exist, the application will create a dummy audio file for testing purposes.

## Application Behavior

- The application will start and display the 3D visualization window
- Audio will begin playing automatically after a short delay
- The visualization will respond to the audio in real-time
- The application will continue running until you close the window
- No automatic exit - the application stays open until manually closed
