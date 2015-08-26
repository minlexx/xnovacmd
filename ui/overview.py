from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from .xn_world import XNovaWorld
from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


# Manages "Overview" tab widget
class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super(OverviewWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/overview.ui'
        # objects, sub-windows
        self.ui = None
        self.world = XNovaWorld()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        # testing only
        self.ui.btn_start.clicked.connect(self.on_btn_start)
        self.ui.btn_stop.clicked.connect(self.on_btn_stop)
        # self.ui.btn_signal.clicked.connect(self.on_btn_signal)

    # testing only
    @pyqtSlot()
    def on_btn_start(self):
        if not self.world.isRunning():
            logger.debug('starting')
            self.world.start()

    # testing only
    @pyqtSlot()
    def on_btn_stop(self):
        if self.world.isRunning():
            logger.debug('stopping')
            self.world.quit()
