import sys
import os
import asyncio
import speech_recognition as sr
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from .saba_window import SabaWindow
from services.chat_service import ChatService

class SpeechWorker(QThread):
    """Worker thread to handle speech recognition without blocking the UI."""
    speech_recognized = pyqtSignal(str)
    speech_error = pyqtSignal(str)
    
    def __init__(self, chat_service):
        super().__init__()
        self.chat_service = chat_service
        
    def run(self):
        """Run speech recognition in a separate thread."""
        try:
            text = self.chat_service.speech_service.listen()
            if text:
                self.speech_recognized.emit(text)
            else:
                self.speech_error.emit("No speech detected.")
        except sr.WaitTimeoutError:
            self.speech_error.emit("Listening timed out - no speech detected.")
        except Exception as e:
            self.speech_error.emit(f"Error during speech recognition: {str(e)}")

class SabaUIManager:
    """
    UI Manager for Saba with integrated speech functionality.
    Provides a simple interface for main to start the UI with speech interaction.
    """
    
    def __init__(self):
        self.app = None
        self.window = None
        self.chat_service = None
        self.speech_worker = None
        
    def initialize(self):
        """Initialize the UI manager with all necessary components."""
        # Initialize chat service
        self.chat_service = ChatService()
        asyncio.run(self.chat_service.initialize())
        
        # Create QApplication if it doesn't exist
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication(sys.argv)
            
            # Set application properties
            self.app.setApplicationName("Saba")
            self.app.setApplicationVersion("1.0")
            self.app.setOrganizationName("Saba Project")
        else:
            self.app = QtWidgets.QApplication.instance()
        
        # Check if output.wav exists, create dummy if not
        wav_path = 'output.wav'
        if not os.path.exists(wav_path):
            self._create_dummy_audio(wav_path)
        
        # Create and setup the main window
        self.window = SabaWindow(wav_path)
        
    def _create_dummy_audio(self, wav_path):
        """Create a dummy audio file for testing if the real one doesn't exist."""
        print(f"Warning: {wav_path} not found. Creating a dummy file for testing.")
        try:
            import numpy as np
            import soundfile as sf
            # Generate a simple sine wave
            sample_rate = 24000
            duration = 5.0  # 5 seconds
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
            sf.write(wav_path, audio, sample_rate)
            print(f"Created dummy audio file: {wav_path}")
        except Exception as e:
            print(f"Could not create dummy audio file: {e}")
    
    def start_with_speech(self):
        """
        Start the application with UI and automatic speech interaction.
        This will show the UI and begin listening for speech.
        Returns when the UI is closed.
        """
        if not self.window:
            raise RuntimeError("UI Manager not initialized. Call initialize() first.")
        
        print("Starting Saba application...")
        
        # Show the window
        self.window.show()
        print("Saba UI window opened.")
        
        # Start with welcome message instead of playing existing audio
        self._start_with_welcome()
        
        # Keep the application running until manually closed
        print("Saba application started with speech interaction. Close the window to exit.")
        return self.app.exec_()
    
    def play(self):
        """
        Public play method that main can invoke to trigger audio playback.
        """
        if self.window and self.window.gl:
            self.window.gl.play_audio()
        else:
            print("UI not initialized - call initialize() first")
    
    def _start_speech_interaction(self):
        """Start the speech interaction loop."""
        # Start listening for speech immediately
        self._listen_for_speech()
        
    def _start_with_welcome(self):
        """Start with a welcome message, then begin speech interaction."""
        # Synthesize and play welcome message
        asyncio.run(self._play_welcome_message())
        
    async def _play_welcome_message(self):
        """Synthesize and play the welcome message."""
        try:
            # Get welcome message from chat service
            welcome_text = await self.chat_service.get_welcome_message()
            print(f"Welcome message: {welcome_text}")
            
            # Synthesize the welcome message
            await self.chat_service.synthesize_response(welcome_text)
            print("Welcome message synthesized to output.wav")
            
            # Update the window with new audio file and play it
            if self.window and self.window.gl:
                self.window.gl.load_audio('output.wav')
                self.window.gl.play_audio()
            
            # Wait a bit for the welcome message to finish, then start listening
            QTimer.singleShot(4000, self._start_speech_interaction)
                
        except Exception as e:
            print(f"Error during welcome message: {e}")
            # If welcome fails, just start listening
            QTimer.singleShot(1000, self._start_speech_interaction)
        
    def _listen_for_speech(self):
        """Start speech recognition in a separate thread."""
        print("Say something...")
        
        # Create and start worker thread
        self.speech_worker = SpeechWorker(self.chat_service)
        self.speech_worker.speech_recognized.connect(self._on_speech_recognized)
        self.speech_worker.speech_error.connect(self._on_speech_error)
        self.speech_worker.finished.connect(self._on_speech_finished)
        self.speech_worker.start()
    
    def _on_speech_recognized(self, text):
        """Handle recognized speech."""
        print(f"You said: {text}")
        
        # Process with chat service and synthesize response asynchronously
        asyncio.run(self._process_and_respond(text))
    
    async def _process_and_respond(self, user_text):
        """Process user input through chat service and respond."""
        try:
            # Process the user input through chat service
            response = await self.chat_service.process_user_input(user_text)
            
            if response:
                # Synthesize the response
                await self.chat_service.synthesize_response(response)
                print("Response synthesized to output.wav")
                
                # Update the window with new audio file and play it
                if self.window and self.window.gl:
                    self.window.gl.load_audio('output.wav')
                    self.window.gl.play_audio()
            
            # Wait a bit before listening again
            QTimer.singleShot(3000, self._listen_for_speech)
                
        except Exception as e:
            print(f"Error during processing: {e}")
            # Try to listen again after error
            QTimer.singleShot(2000, self._listen_for_speech)
    
    def _on_speech_error(self, error_message):
        """Handle speech recognition errors."""
        print(error_message)
        
        # Wait a bit before trying again
        QTimer.singleShot(2000, self._listen_for_speech)
    
    def _on_speech_finished(self):
        """Handle speech worker thread completion."""
        self.speech_worker = None
