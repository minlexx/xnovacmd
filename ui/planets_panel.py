from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFrame, QMessageBox
from PyQt5.QtGui import QIcon, QPaintEvent, QPainter, QFont

from .xnova.xn_data import XNPlanet
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class PlanetWidget(QFrame):
    def __init__(self, parent=None):
        super(PlanetWidget, self).__init__(parent)
        self._planet = XNPlanet()
        self.init_ui()

    def init_ui(self):
        # logger.debug('PlanetWidget init UI')
        self.setMinimumSize(100, 100)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.StyledPanel)

    def setPlanet(self, p: XNPlanet):
        self._planet = p

    def paintEvent(self, e: QPaintEvent):
        super(PlanetWidget, self).paintEvent(e)
        painter = QPainter(self)
        painter.setPen(Qt.blue)
        painter.setFont(QFont("Arial", 30))
        painter.drawText(self.rect(), Qt.AlignCenter, self._planet.name)
