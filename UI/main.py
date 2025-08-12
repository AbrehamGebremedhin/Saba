import sys
import os
from PyQt5 import QtWidgets

from .saba_window import SabaWindow

def main():
    """Main entry point for the Saba application."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Saba")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Saba Project")
    
    # Check if output.wav exists
    wav_path = 'output.wav'
    if not os.path.exists(wav_path):
        print(f"Warning: {wav_path} not found. Creating a dummy file for testing.")
        # Create a dummy audio file for testing if the real one doesn't exist
        import numpy as np
        import soundfile as sf
        # Generate a simple sine wave
        sample_rate = 24000
        duration = 5.0  # 5 seconds
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        sf.write(wav_path, audio, sample_rate)
        print(f"Created dummy audio file: {wav_path}")
    
    # Create and show the main window
    window = SabaWindow(wav_path)
    window.show()
    
    # Keep the application running until manually closed
    print("Saba application started. Close the window to exit.")
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
