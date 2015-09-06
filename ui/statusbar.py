from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QStatusBar, QPushButton
from PyQt5.QtGui import QIcon

from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class XNCStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super(XNCStatusBar, self).__init__(parent)
        # state vars
        self.world = XNovaWorld_instance()
        # initialization
        self.setSizeGripEnabled(True)
        # testing only
        self.btn_start = QPushButton(self.tr('start'), self)
        self.btn_stop = QPushButton(self.tr('stop'), self)
        self.btn_signal = QPushButton(self.tr('signal'), self)
        # void	addPermanentWidget(QWidget * widget, int stretch = 0)
        self.addPermanentWidget(self.btn_start, 0)
        self.addPermanentWidget(self.btn_stop, 0)
        self.addPermanentWidget(self.btn_signal, 0)
        self.btn_start.clicked.connect(self.on_btn_start)
        self.btn_stop.clicked.connect(self.on_btn_stop)
        self.btn_signal.clicked.connect(self.on_btn_signal)
        #
        self.show()
        # self.showMessage('wow')

    def setupUi(self):
        pass

    def setStatus(self, msg: str, timeout: int=0):
        self.showMessage(msg, timeout)

# some functions may be useful, documentation:
# void QStatusBar::clearMessage()
# void QStatusBar::addPermanentWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::addWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::removeWidget(QWidget * widget)

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

    @pyqtSlot()
    def on_btn_signal(self):
        # test exceptions in pyQt slots
        raise Exception("wow")

