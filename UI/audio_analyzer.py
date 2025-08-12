import time
import numpy as np
import soundfile as sf
import threading
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not available, audio playback disabled")

FFT_SIZE = 1024

class AudioAnalyzer:
    def __init__(self, wav_path):
        data, sr = sf.read(wav_path, always_2d=True)
        if data.ndim > 1:
            data = data.mean(axis=1)
        self.audio = data.astype(np.float32)
        self.sr = sr
        self.wav_path = wav_path
        self.start_time = None
        
        # Initialize pygame mixer for audio playback
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.pre_init(frequency=sr, size=-16, channels=1, buffer=1024)
                pygame.mixer.init()
                print("Pygame audio initialized")
            except Exception as e:
                print(f"Failed to initialize pygame audio: {e}")

    def play(self):
        """Start audio playback using pygame mixer."""
        if not PYGAME_AVAILABLE:
            print("Audio playback disabled - pygame not available")
            self.start_time = time.time()
            return
            
        try:
            # Load and play the audio file directly
            sound = pygame.mixer.Sound(self.wav_path)
            sound.play()
            print("Audio playback started with pygame")
            
        except Exception as e:
            print(f"Audio playback failed: {e}")
        
        # Always set start_time regardless of playback success
        self.start_time = time.time()
    
    def stop(self):
        """Stop audio playback safely."""
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.stop()
                print("Audio stopped")
        except Exception as e:
            print(f"Error stopping audio: {e}")
        finally:
            self.start_time = None

    def analyze(self):
        if self.start_time is None:
            return 0.0, None
        elapsed = time.time() - self.start_time
        idx = int(elapsed * self.sr)
        
        # Check if audio has finished playing
        audio_duration = len(self.audio) / self.sr
        if elapsed > audio_duration:
            # Audio has finished, return minimal values to keep visualization going
            return 0.0, None
            
        win = int(self.sr * 0.02)
        i0, i1 = max(0, idx - win // 2), min(len(self.audio), idx + win // 2)
        window = self.audio[i0:i1] if i1 > i0 else np.zeros(win)
        rms = float(np.sqrt(np.mean(window ** 2)))
        if len(window) >= 8:
            fft = np.fft.rfft(window * np.hanning(len(window)), n=FFT_SIZE)
            spec = np.abs(fft)
            spec /= np.max(spec) + 1e-9
        else:
            spec = None
        return rms, spec
