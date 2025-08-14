from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtWidgets import QLabel, QTextEdit, QProgressBar, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsOpacityEffect

from .saba_gl import SabaGL

class ModernSubtitleWidget(QtWidgets.QWidget):
    """Modern subtitle-style overlay for speech transcription"""
    
    def __init__(self):
        super().__init__()
        self.current_text = ""
        self.fade_timer = QTimer()
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.fade_out)
        
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 15, 25, 0.85),
                    stop: 0.5 rgba(0, 20, 35, 0.9),
                    stop: 1 rgba(0, 15, 25, 0.85));
                color: rgba(200, 240, 255, 0.95);
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 18px;
                font-weight: 300;
                padding: 16px 32px;
                border-radius: 12px;
                border: 1px solid rgba(100, 200, 255, 0.3);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        
        # Initially hidden
        self.setVisible(False)
        
    def show_subtitle(self, text, speaker="", duration=4000):
        """Show subtitle with fade in/out animation - JARVIS style"""
        if speaker and speaker.upper() != "SYSTEM":
            if speaker.upper() == "USER":
                display_text = text
                self.subtitle_label.setStyleSheet("""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 rgba(0, 25, 50, 0.85),
                        stop: 0.5 rgba(0, 35, 60, 0.9),
                        stop: 1 rgba(0, 25, 50, 0.85));
                    color: rgba(180, 220, 255, 0.95);
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 18px;
                    font-weight: 300;
                    padding: 16px 32px;
                    border-radius: 12px;
                    border: 1px solid rgba(100, 180, 255, 0.4);
                """)
            else:  # SABA
                display_text = text
                self.subtitle_label.setStyleSheet("""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 rgba(0, 15, 25, 0.85),
                        stop: 0.5 rgba(0, 20, 35, 0.9),
                        stop: 1 rgba(0, 15, 25, 0.85));
                    color: rgba(200, 240, 255, 0.95);
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 18px;
                    font-weight: 300;
                    padding: 16px 32px;
                    border-radius: 12px;
                    border: 1px solid rgba(120, 200, 255, 0.4);
                """)
        else:
            display_text = text
            
        self.current_text = display_text
        self.subtitle_label.setText(display_text)
        
        # Fade in
        self.setVisible(True)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Set timer to fade out
        self.fade_timer.start(duration)
        
    def fade_out(self):
        """Fade out the subtitle"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(lambda: self.setVisible(False))
        self.fade_animation.start()
        
    def update_position(self, parent_size):
        """Update position to stay at bottom center of parent - JARVIS style"""
        subtitle_height = 100
        margin = 80
        width = min(900, parent_size.width() - 120)
        
        x = (parent_size.width() - width) // 2
        y = parent_size.height() - subtitle_height - margin
        
        self.setGeometry(x, y, width, subtitle_height)

class ModernStatusWidget(QtWidgets.QWidget):
    """Minimal JARVIS-style status indicator"""
    
    def __init__(self):
        super().__init__()
        self.current_status = "Standby"
        self.is_listening = False
        self.setup_ui()
        
        # Subtle breathing animation for listening state
        self.opacity_effect = QGraphicsOpacityEffect()
        self.status_indicator.setGraphicsEffect(self.opacity_effect)
        
        self.breathing_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.breathing_animation.setDuration(3000)  # Slower, more organic
        self.breathing_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.breathing_animation.setLoopCount(-1)
        
    def setup_ui(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedHeight(60)  # Increased height to prevent overlap
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(20)
        
        # Status indicator (subtle animated dot)
        self.status_indicator = QtWidgets.QLabel("●")
        self.status_indicator.setStyleSheet("""
            color: rgba(100, 200, 255, 0.6);
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_indicator)
        
        # Status text - more JARVIS-like
        self.status_label = QLabel("STANDBY")
        self.status_label.setStyleSheet("""
            color: rgba(200, 240, 255, 0.7);
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 11px;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 2px;
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # System time - more subtle
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            color: rgba(150, 200, 255, 0.4);
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10px;
            font-weight: 300;
        """)
        layout.addWidget(self.time_label)
        
        # Update time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        
    def update_time(self):
        """Update the time display"""
        current_time = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        self.time_label.setText(current_time)
        
    def set_status(self, status, is_processing=False):
        """Update status with subtle visual feedback - JARVIS style"""
        self.current_status = status
        self.status_label.setText(status.upper())
        
        if status.lower() == "listening":
            self.is_listening = True
            self.status_indicator.setStyleSheet("""
                color: rgba(100, 255, 200, 0.8);
                font-size: 14px;
                font-weight: bold;
            """)
            # Start subtle breathing animation
            self.breathing_animation.setStartValue(0.6)
            self.breathing_animation.setEndValue(1.0)
            self.breathing_animation.start()
            
        elif status.lower() == "processing" or is_processing:
            self.is_listening = False
            self.breathing_animation.stop()
            self.status_indicator.setStyleSheet("""
                color: rgba(255, 220, 100, 0.8);
                font-size: 14px;
                font-weight: bold;
            """)
            
        elif status.lower() == "playing audio":
            self.is_listening = False
            self.breathing_animation.stop()
            self.status_indicator.setStyleSheet("""
                color: rgba(100, 200, 255, 0.9);
                font-size: 14px;
                font-weight: bold;
            """)
            
        else:  # Standby
            self.is_listening = False
            self.breathing_animation.stop()
            self.status_indicator.setStyleSheet("""
                color: rgba(100, 200, 255, 0.6);
                font-size: 14px;
                font-weight: bold;
            """)

class ModernControlWidget(QtWidgets.QWidget):
    """Single minimal exit button"""
    
    exit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 100, 100, 0.25),
                    stop: 1 rgba(200, 50, 50, 0.35));
                border: 1px solid rgba(255, 100, 100, 0.4);
                border-radius: 18px;
                color: rgba(255, 255, 255, 0.9);
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 50px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 120, 120, 0.4),
                    stop: 1 rgba(220, 80, 80, 0.5));
                border: 1px solid rgba(255, 150, 150, 0.6);
                color: rgba(255, 255, 255, 1.0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(200, 80, 80, 0.6),
                    stop: 1 rgba(160, 40, 40, 0.7));
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Single exit button
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        layout.addWidget(self.exit_btn)

    def update_position(self, parent_size):
        """Update position to float at top right, avoiding overlaps"""
        control_width = 70
        control_height = 36
        margin = 20
        
        x = parent_size.width() - control_width - margin
        y = margin + 60  # Move down to avoid status overlap
        
        self.setGeometry(x, y, control_width, control_height)

class SabaWindow(QtWidgets.QWidget):
    # Signals for communication with UI manager
    user_speech_detected = pyqtSignal(str)
    user_speech_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    status_changed = pyqtSignal(str, bool)  # status, show_progress
    
    def __init__(self, wav_path):
        super().__init__()
        self.wav_path = wav_path
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        
        # Window dragging
        self.drag_pos = None
        
    def setup_window(self):
        """Setup the main window properties"""
        # Remove the default window frame but keep it as a normal window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # Set window properties
        self.setWindowTitle("SABA - AI Interface")
        self.resize(1400, 900)
        
        # Center the window on screen
        screen = QtWidgets.QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2))
        
        # Modern dark gradient background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(8, 12, 20, 0.98),
                    stop: 0.5 rgba(15, 20, 30, 0.98),
                    stop: 1 rgba(10, 15, 25, 0.98));
                border: 1px solid rgba(100, 150, 255, 0.3);
                border-radius: 12px;
            }
        """)
        
    def setup_ui(self):
        """Setup the modern minimal user interface"""
        # Main layout with no margins for full-screen effect
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main 3D visualization takes full window
        self.gl = SabaGL(self.wav_path)
        main_layout.addWidget(self.gl)
        
        # Status overlay (top)
        self.status_widget = ModernStatusWidget()
        self.status_widget.setParent(self)
        
        # Subtitle overlay (bottom center)
        self.subtitle_widget = ModernSubtitleWidget()
        self.subtitle_widget.setParent(self)
        
        # Control overlay (bottom right)
        self.control_widget = ModernControlWidget()
        self.control_widget.setParent(self)
        
        # Position overlays
        self.update_overlay_positions()
        
    def resizeEvent(self, event):
        """Handle window resize to reposition overlays"""
        super().resizeEvent(event)
        self.update_overlay_positions()
        
    def update_overlay_positions(self):
        """Update positions of floating overlay widgets"""
        size = self.size()
        
        # Status widget at top
        self.status_widget.setGeometry(0, 0, size.width(), 60)
        
        # Update subtitle and control positions
        self.subtitle_widget.update_position(size)
        self.control_widget.update_position(size)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect control widget signals
        self.control_widget.exit_requested.connect(self.close)
        
        # Connect GL widget signals
        self.gl.status_update.connect(self.on_status_update)
        
    def request_listen(self):
        """Request to start listening for speech - triggered automatically"""
        self.user_speech_requested.emit()
        
    def request_stop(self):
        """Request to stop current operation"""
        self.stop_requested.emit()
        
    def on_status_update(self, status, show_progress=False):
        """Handle status updates from the GL widget"""
        self.status_widget.set_status(status, show_progress)
        
    def add_user_speech(self, text):
        """Show user speech as subtitle"""
        self.subtitle_widget.show_subtitle(text, "USER", duration=3000)
        
    def add_assistant_response(self, text):
        """Show assistant response as subtitle"""
        self.subtitle_widget.show_subtitle(text, "SABA", duration=5000)
        
    def add_system_message(self, text):
        """Show system message as brief subtitle"""
        self.subtitle_widget.show_subtitle(text, "SYSTEM", duration=2000)
        
    def set_status(self, status, show_progress=False):
        """Update the status display"""
        self.status_widget.set_status(status, show_progress)
        
    def set_connection_status(self, online=True):
        """Connection status integrated into main status"""
        pass  # Modern UI doesn't need separate connection status
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts - simplified for JARVIS-like experience"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
        
    # Mouse event handlers for window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
