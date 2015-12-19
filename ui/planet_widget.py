from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QMenu, QAction, \
    QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIcon, QCursor

from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger


logger = xn_logger.get(__name__, debug=True)


class PlanetWidget(QFrame):
    """
    Provides view of galaxy/solarsystem contents as table widget
    """
    def __init__(self, parent: QWidget):
        super(PlanetWidget, self).__init__(parent)
        self.world = XNovaWorld_instance()
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self.setLayout(self._layout)
