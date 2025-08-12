from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from .saba_gl import SabaGL

class SabaWindow(QtWidgets.QWidget):
    def __init__(self, wav_path):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.gl = SabaGL(wav_path)
        layout.addWidget(self.gl)
        self.resize(1100, 800)
