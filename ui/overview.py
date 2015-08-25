from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class BGThread(QThread):
    def __init__(self, parent=None):
        super(BGThread, self).__init__(parent)
        self.cookies_dict = {}

    def init_cookies(self, cd: dict):
        self.cookies_dict = cd

    def run(self):
        logger.debug('BGThread: entering event loop')
        ret = self.exec()
        logger.debug('BGThread: event loop ended with code {0}'.format(ret))
        # cannot return result

    @pyqtSlot()
    def on_signal(self):
        logger.debug('Thread on_signal, cur thread: {0}'.format(QThread.currentThread()))


class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super(OverviewWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/overview.ui'
        # objects, sub-windows
        self.ui = None
        self.th = BGThread(self)
        # initialization
        self.load_ui()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        self.ui.btn_start.clicked.connect(self.on_btn_start)
        self.ui.btn_stop.clicked.connect(self.on_btn_stop)
        self.ui.btn_signal.clicked.connect(self.on_btn_signal)

    testSignal = pyqtSignal()

    @pyqtSlot()
    def on_btn_start(self):
        logger.debug('click start')
        self.testSignal.connect(self.th.on_signal, Qt.QueuedConnection)
        self.th.start()

    @pyqtSlot()
    def on_btn_stop(self):
        logger.debug('click stop')
        self.th.quit()

    @pyqtSlot()
    def on_btn_signal(self):
        logger.debug('click signal, cur thread: {0}'.format(QThread.currentThread()))
        self.testSignal.emit()
