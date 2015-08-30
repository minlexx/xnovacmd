from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox, QToolButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class FlightsWidget(QWidget):
    def __init__(self, parent=None):
        super(FlightsWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/flights_widget.ui'
        # objects, sub-windows
        self.ui = None

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        logger.debug('FlightsWidget loaded UI')
        self.ui.tw_flights.hide()
        self.btn_show.clicked.connect(self.on_showhide_fleets)

    @pyqtSlot()
    def on_showhide_fleets(self):
        if self.ui.tw_flights.isVisible():
            self.ui.tw_flights.hide()
            self.setMinimumHeight(22)
            self.parent().setMinimumHeight(22)
            self.btn_show.setArrowType(Qt.RightArrow)
        else:
            self.ui.tw_flights.show()
            self.setMinimumHeight(22+22+2)
            self.parent().setMinimumHeight(22+22+3)
            self.btn_show.setArrowType(Qt.DownArrow)
