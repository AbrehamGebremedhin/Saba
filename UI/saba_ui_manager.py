import sys
import os
import asyncio
import speech_recognition as sr
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from .saba_window import SabaWindow
from services.chat_service import ChatService
from config.logger import get_logger

logger = get_logger(__name__)

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
            logger.error(f"Speech recognition error in worker thread: {str(e)}")

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
        # Use run_until_complete to initialize async chat service safely
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already running (e.g., in Jupyter or PyQt), schedule as a task
            asyncio.create_task(self.chat_service.initialize())
        else:
            loop.run_until_complete(self.chat_service.initialize())

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
        
        # Connect window signals
        self.window.user_speech_requested.connect(self._listen_for_speech)
        self.window.stop_requested.connect(self._stop_current_operation)
        
    def _create_dummy_audio(self, wav_path):
        """Create a dummy audio file for testing if the real one doesn't exist."""
        logger.warning(f"Warning: {wav_path} not found. Creating a dummy file for testing.")
        try:
            import numpy as np
            import soundfile as sf
            # Generate a simple sine wave
            sample_rate = 24000
            duration = 5.0  # 5 seconds
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
            sf.write(wav_path, audio, sample_rate)
            logger.info(f"Created dummy audio file: {wav_path}")
        except Exception as e:
            logger.error(f"Could not create dummy audio file: {e}")
    
    def start_with_speech(self):
        """
        Start the application with UI and automatic speech interaction.
        This will show the UI and begin listening for speech.
        Returns when the UI is closed.
        """
        if not self.window:
            raise RuntimeError("UI Manager not initialized. Call initialize() first.")
        
        logger.info("Starting Saba application...")
        
        # Show the window
        self.window.show()
        logger.info("Saba UI window opened.")
        
        # Start with welcome message instead of playing existing audio
        self._start_with_welcome()
        
        # Keep the application running until manually closed
        logger.info("Saba application started with speech interaction. Close the window to exit.")
        return self.app.exec_()
    
    def play(self):
        """
        Public play method that main can invoke to trigger audio playback.
        """
        if self.window and self.window.gl:
            self.window.gl.play_audio()
        else:
            logger.warning("UI not initialized - call initialize() first")
    
    def _start_speech_interaction(self):
        """Start the speech interaction loop after audio playback is finished."""
        if self.window and self.window.gl:
            # Connect to the audio finished signal, so we only listen after playback
            try:
                self.window.gl.audio_finished.disconnect(self._listen_for_speech)
            except Exception:
                pass  # Ignore if not connected
            self.window.gl.audio_finished.connect(self._listen_for_speech)
            # If audio is not playing, start listening immediately
            if not getattr(self.window.gl, 'is_audio_playing', lambda: False)():
                self._listen_for_speech()
        else:
            self._listen_for_speech()
        
    def _start_with_welcome(self):
        """Start with a welcome message, then begin speech interaction."""
        # Add welcome message to transcription
        if self.window:
            self.window.add_system_message("Initializing J.A.R.V.I.S Interface...")
        
        # Synthesize and play welcome message
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self._play_welcome_message())
        else:
            loop.run_until_complete(self._play_welcome_message())
        
    async def _play_welcome_message(self):
        """Synthesize and play the welcome message."""
        try:
            # Set thinking mode
            if self.window and self.window.gl:
                self.window.gl.set_thinking_mode(True)
                self.window.set_status("Initializing", True)
            
            # Get welcome message from chat service
            welcome_text = await self.chat_service.get_welcome_message()
            logger.info(f"Welcome message: {welcome_text}")
            
            # Add to transcription
            if self.window:
                self.window.add_assistant_response(welcome_text)
            
            # Synthesize the welcome message
            await self.chat_service.synthesize_response(welcome_text)
            logger.info("Welcome message synthesized to output.wav")
            
            # Update the window with new audio file and play it
            if self.window and self.window.gl:
                self.window.gl.set_thinking_mode(False)
                self.window.gl.load_audio('output.wav')
                self.window.gl.play_audio()
                self.window.set_status("Playing Audio", False)
            
            # Start speech interaction only after audio finishes
            self._start_speech_interaction()
                
        except Exception as e:
            logger.error(f"Error during welcome message: {e}")
            if self.window:
                self.window.add_system_message(f"Error: {str(e)}")
                self.window.set_status("Error", False)
                if self.window.gl:
                    self.window.gl.set_thinking_mode(False)
            # If welcome fails, just start listening
            QTimer.singleShot(1000, self._start_speech_interaction)
        
    def _listen_for_speech(self):
        """Start speech recognition in a separate thread."""
        logger.info("Say something...")
        
        # Update UI to show listening state
        if self.window:
            self.window.add_system_message("Listening...")
            self.window.set_status("Listening", False)
        
        # Create and start worker thread
        self.speech_worker = SpeechWorker(self.chat_service)
        self.speech_worker.speech_recognized.connect(self._on_speech_recognized)
        self.speech_worker.speech_error.connect(self._on_speech_error)
        self.speech_worker.finished.connect(self._on_speech_finished)
        self.speech_worker.start()
    
    def _on_speech_recognized(self, text):
        """Handle recognized speech."""
        logger.info(f"You said: {text}")
        
        # Add to transcription
        if self.window:
            self.window.add_user_speech(text)
            self.window.set_status("Processing", True)
        
        # Process with chat service and synthesize response asynchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self._process_and_respond(text))
        else:
            loop.run_until_complete(self._process_and_respond(text))
    
    async def _process_and_respond(self, user_text):
        """Process user input through chat service and respond."""
        try:
            # Set thinking mode
            if self.window and self.window.gl:
                self.window.gl.set_thinking_mode(True)
            
            # Process the user input through chat service
            response = await self.chat_service.process_user_input(user_text)
            
            if response:
                # Add response to transcription
                if self.window:
                    self.window.add_assistant_response(response)
                
                # Synthesize the response
                await self.chat_service.synthesize_response(response)
                logger.info("Response synthesized to output.wav")
                
                # Update the window with new audio file and play it
                if self.window and self.window.gl:
                    self.window.gl.set_thinking_mode(False)
                    self.window.gl.load_audio('output.wav')
                    self.window.gl.play_audio()
                    self.window.set_status("Playing Audio", False)
            
            # Start speech interaction only after audio finishes
            self._start_speech_interaction()
                
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            if self.window:
                self.window.add_system_message(f"Processing error: {str(e)}")
                self.window.set_status("Error", False)
                if self.window.gl:
                    self.window.gl.set_thinking_mode(False)
            # Try to listen again after error
            QTimer.singleShot(2000, self._listen_for_speech)
    
    def _on_speech_error(self, error_message):
        """Handle speech recognition errors."""
        logger.warning(error_message)
        
        # Update UI
        if self.window:
            self.window.add_system_message(error_message)
            self.window.set_status("Standby", False)
        
        # Wait a bit before trying again
        QTimer.singleShot(2000, self._listen_for_speech)
    
    def _on_speech_finished(self):
        """Handle speech worker thread completion."""
        self.speech_worker = None
        
    def _stop_current_operation(self):
        """Stop the current operation (speech recognition, audio playback, etc.)"""
        try:
            # Stop speech worker if running
            if self.speech_worker and self.speech_worker.isRunning():
                self.speech_worker.terminate()
                self.speech_worker.wait(1000)  # Wait up to 1 second
                self.speech_worker = None
                
            # Stop audio playback
            if self.window and self.window.gl:
                if hasattr(self.window.gl.audio, 'stop'):
                    self.window.gl.audio.stop()
                self.window.gl.set_thinking_mode(False)
                
            # Update UI
            if self.window:
                self.window.add_system_message("Operation stopped by user")
                self.window.set_status("Standby", False)
                
            logger.info("Current operation stopped by user")
            
        except Exception as e:
            logger.error(f"Error stopping operation: {e}")
            if self.window:
                self.window.add_system_message(f"Stop error: {str(e)}")
                self.window.set_status("Error", False)
