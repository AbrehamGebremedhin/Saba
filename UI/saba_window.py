from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtWidgets import QLabel, QTextEdit, QProgressBar, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsOpacityEffect

from .saba_gl import SabaGL
from .color_scheme import color_scheme
from .typography import typography

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
        
        # Get dynamic colors from color scheme
        bg_color = color_scheme.palette.bg_transparent_blue
        text_color = color_scheme.palette.text_primary
        border_color = color_scheme.get_color('accent', 0.3)
        
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
            }}
            QLabel {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba({int(bg_color[0]*255)}, {int(bg_color[1]*255)}, {int(bg_color[2]*255)}, {bg_color[3]}),
                    stop: 0.5 rgba({int(bg_color[0]*255*1.2)}, {int(bg_color[1]*255*1.2)}, {int(bg_color[2]*255*1.2)}, {bg_color[3]*1.1}),
                    stop: 1 rgba({int(bg_color[0]*255)}, {int(bg_color[1]*255)}, {int(bg_color[2]*255)}, {bg_color[3]}));
                color: rgba({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)}, 0.95);
                font-family: '{typography.loaded_fonts.get("secondary", "Arial")}', 'Arial', sans-serif;
                font-size: 18px;
                font-weight: 300;
                padding: 16px 32px;
                border-radius: 12px;
                border: 1px solid rgba({int(border_color[0]*255)}, {int(border_color[1]*255)}, {int(border_color[2]*255)}, {border_color[3]});
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setFont(typography.get_body_font(18))
        layout.addWidget(self.subtitle_label)
        
        # Initially hidden
        self.setVisible(False)
        
    def show_subtitle(self, text, speaker="", duration=4000):
        """Show subtitle with fade in/out animation - Enhanced JARVIS style"""
        if speaker and speaker.upper() != "SYSTEM":
            if speaker.upper() == "USER":
                display_text = text
                # Dynamic user styling
                user_bg = color_scheme.palette.bg_transparent_dark
                user_text = color_scheme.palette.info_bright
                user_border = color_scheme.get_color('info_base', 0.4)
                
                self.subtitle_label.setStyleSheet(f"""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 rgba({int(user_bg[0]*255)}, {int(user_bg[1]*255)}, {int(user_bg[2]*255)}, {user_bg[3]}),
                        stop: 0.5 rgba({int(user_bg[0]*255*1.3)}, {int(user_bg[1]*255*1.3)}, {int(user_bg[2]*255*1.3)}, {user_bg[3]*1.1}),
                        stop: 1 rgba({int(user_bg[0]*255)}, {int(user_bg[1]*255)}, {int(user_bg[2]*255)}, {user_bg[3]}));
                    color: rgba({int(user_text[0]*255)}, {int(user_text[1]*255)}, {int(user_text[2]*255)}, 0.95);
                    font-family: '{typography.loaded_fonts.get("secondary", "Arial")}', 'Arial', sans-serif;
                    font-size: 18px;
                    font-weight: 300;
                    padding: 16px 32px;
                    border-radius: 12px;
                    border: 1px solid rgba({int(user_border[0]*255)}, {int(user_border[1]*255)}, {int(user_border[2]*255)}, {user_border[3]});
                """)
            else:  # SABA
                display_text = text
                # Dynamic SABA styling
                saba_bg = color_scheme.palette.bg_transparent_blue
                saba_text = color_scheme.palette.energy_bright
                saba_border = color_scheme.get_color('primary', 0.4)
                
                self.subtitle_label.setStyleSheet(f"""
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 rgba({int(saba_bg[0]*255)}, {int(saba_bg[1]*255)}, {int(saba_bg[2]*255)}, {saba_bg[3]}),
                        stop: 0.5 rgba({int(saba_bg[0]*255*1.2)}, {int(saba_bg[1]*255*1.2)}, {int(saba_bg[2]*255*1.2)}, {saba_bg[3]*1.1}),
                        stop: 1 rgba({int(saba_bg[0]*255)}, {int(saba_bg[1]*255)}, {int(saba_bg[2]*255)}, {saba_bg[3]}));
                    color: rgba({int(saba_text[0]*255)}, {int(saba_text[1]*255)}, {int(saba_text[2]*255)}, 0.95);
                    font-family: '{typography.loaded_fonts.get("primary", "Arial")}', 'Arial', sans-serif;
                    font-size: 18px;
                    font-weight: 400;
                    padding: 16px 32px;
                    border-radius: 12px;
                    border: 1px solid rgba({int(saba_border[0]*255)}, {int(saba_border[1]*255)}, {int(saba_border[2]*255)}, {saba_border[3]});
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
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(20)
        
        # Status indicator (enhanced animated dot)
        self.status_indicator = QtWidgets.QLabel("●")
        indicator_color = color_scheme.get_color('accent', 0.6)
        self.status_indicator.setStyleSheet(f"""
            color: rgba({int(indicator_color[0]*255)}, {int(indicator_color[1]*255)}, {int(indicator_color[2]*255)}, {indicator_color[3]});
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_indicator)
        
        # Status text - Enhanced JARVIS-like with dynamic colors
        self.status_label = QLabel("STANDBY")
        self.status_label.setFont(typography.get_status_font(10))
        
        # Futuristic cyan color for status text
        status_color = (0.0, 0.8, 1.0, 0.8)  # Bright cyan
        self.status_label.setStyleSheet(f"""
            color: rgba({int(status_color[0]*255)}, {int(status_color[1]*255)}, {int(status_color[2]*255)}, {status_color[3]});
            font-family: '{typography.loaded_fonts.get("secondary", "Arial")}', 'Arial', sans-serif;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 2px;
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # System time - Futuristic pale green styling
        self.time_label = QLabel()
        self.time_label.setFont(typography.get_mono_font(10))
        time_color = (0.4, 1.0, 0.6, 0.7)  # Pale yellow-green
        self.time_label.setStyleSheet(f"""
            color: rgba({int(time_color[0]*255)}, {int(time_color[1]*255)}, {int(time_color[2]*255)}, {time_color[3]});
            font-family: '{typography.loaded_fonts.get("monospace", "Consolas")}', 'Consolas', monospace;
            font-size: 10px;
            font-weight: 400;
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
        """Update status with JARVIS-style bright cyan for LISTENING."""
        self.current_status = status
        self.status_label.setText(status.upper())
        
        if status.lower() == "listening":
            self.is_listening = True
            # Bright cyan color for LISTENING - JARVIS style
            listening_color = (0.0, 0.8, 1.0, 0.95)  # Bright cyan
            self.status_indicator.setStyleSheet(f"""
                color: rgba({int(listening_color[0]*255)}, {int(listening_color[1]*255)}, {int(listening_color[2]*255)}, {listening_color[3]});
                font-size: 14px;
                font-weight: bold;
            """)
            # Update status label with bright cyan
            self.status_label.setStyleSheet(f"""
                color: rgba({int(listening_color[0]*255)}, {int(listening_color[1]*255)}, {int(listening_color[2]*255)}, {listening_color[3]});
                font-family: '{typography.loaded_fonts.get("secondary", "Arial")}', 'Arial', sans-serif;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 2px;
            """)
            # Start breathing animation
            self.breathing_animation.setStartValue(0.6)
            self.breathing_animation.setEndValue(1.0)
            self.breathing_animation.start()
            
        elif status.lower() == "processing" or is_processing:
            self.is_listening = False
            self.breathing_animation.stop()
            # Warm gold for processing
            processing_color = (1.0, 0.7, 0.2, 0.8)
            self.status_indicator.setStyleSheet(f"""
                color: rgba({int(processing_color[0]*255)}, {int(processing_color[1]*255)}, {int(processing_color[2]*255)}, {processing_color[3]});
                font-size: 14px;
                font-weight: bold;
            """)
            
        elif status.lower() == "playing audio":
            self.is_listening = False
            self.breathing_animation.stop()
            # Green for active audio
            audio_color = (0.2, 1.0, 0.4, 0.9)
            self.status_indicator.setStyleSheet(f"""
                color: rgba({int(audio_color[0]*255)}, {int(audio_color[1]*255)}, {int(audio_color[2]*255)}, {audio_color[3]});
                font-size: 14px;
                font-weight: bold;
            """)
            
        else:  # Standby
            self.is_listening = False
            self.breathing_animation.stop()
            # Dim gray for standby
            standby_color = (0.5, 0.5, 0.6, 0.6)
            self.status_indicator.setStyleSheet(f"""
                color: rgba({int(standby_color[0]*255)}, {int(standby_color[1]*255)}, {int(standby_color[2]*255)}, {standby_color[3]});
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
        
        # Enhanced JARVIS-style bold red colors for EXIT button
        bg_color = (0.9, 0.15, 0.15)  # Slightly brighter red base
        bg_hover = (1.0, 0.3, 0.3)   # Brighter red on hover
        bg_pressed = (0.7, 0.1, 0.1)  # Darker red when pressed
        border_color = (1.0, 0.4, 0.4, 0.8)  # Brighter red border
        border_hover = (1.0, 0.5, 0.5, 1.0)  # Even brighter border on hover
        text_color = (1.0, 1.0, 1.0)  # White text
        
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
            }}
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba({int(bg_color[0]*255)}, {int(bg_color[1]*255)}, {int(bg_color[2]*255)}, 0.85),
                    stop: 1 rgba({int(bg_color[0]*255*0.8)}, {int(bg_color[1]*255*0.8)}, {int(bg_color[2]*255*0.8)}, 0.9));
                border: 2px solid rgba({int(border_color[0]*255)}, {int(border_color[1]*255)}, {int(border_color[2]*255)}, {border_color[3]});
                border-radius: 18px;
                color: rgba({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)}, 0.95);
                font-family: '{typography.loaded_fonts.get("secondary", "Arial")}', 'Arial', sans-serif;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 16px;
                min-width: 50px;
                text-transform: uppercase;
                letter-spacing: 1.2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba({int(bg_hover[0]*255)}, {int(bg_hover[1]*255)}, {int(bg_hover[2]*255)}, 0.9),
                    stop: 1 rgba({int(bg_hover[0]*255*0.8)}, {int(bg_hover[1]*255*0.8)}, {int(bg_hover[2]*255*0.8)}, 0.95));
                border: 2px solid rgba({int(border_hover[0]*255)}, {int(border_hover[1]*255)}, {int(border_hover[2]*255)}, {border_hover[3]});
                color: rgba({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)}, 1.0);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba({int(bg_pressed[0]*255)}, {int(bg_pressed[1]*255)}, {int(bg_pressed[2]*255)}, 1.0),
                    stop: 1 rgba({int(bg_pressed[0]*255*0.6)}, {int(bg_pressed[1]*255*0.6)}, {int(bg_pressed[2]*255*0.6)}, 1.0));
                border: 2px solid rgba({int(border_color[0]*255)}, {int(border_color[1]*255)}, {int(border_color[2]*255)}, {border_color[3]});
                color: rgba({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)}, 1.0);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Enhanced exit button with typography
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.setFont(typography.get_caption_font(11))
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
        """Setup the main window properties with enhanced JARVIS styling"""
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
        
        # Enhanced dark gradient background with dynamic colors
        bg_dark = color_scheme.palette.bg_dark
        bg_medium = color_scheme.palette.bg_medium
        border_color = color_scheme.get_color('accent', 0.3)
        
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba({int(bg_dark[0]*255)}, {int(bg_dark[1]*255)}, {int(bg_dark[2]*255)}, 0.98),
                    stop: 0.5 rgba({int(bg_medium[0]*255)}, {int(bg_medium[1]*255)}, {int(bg_medium[2]*255)}, 0.98),
                    stop: 1 rgba({int(bg_dark[0]*255)}, {int(bg_dark[1]*255)}, {int(bg_dark[2]*255)}, 0.98));
                border: 1px solid rgba({int(border_color[0]*255)}, {int(border_color[1]*255)}, {int(border_color[2]*255)}, {border_color[3]});
                border-radius: 12px;
            }}
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
