from PyQt5.QtCore import pyqtSlot, QCoreApplication
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
        # self.btn_start = QPushButton(self.tr('start'), self)
        # self.btn_stop = QPushButton(self.tr('stop'), self)
        self.btn_test1 = QPushButton(self.tr('test parse'), self)
        # void	addPermanentWidget(QWidget * widget, int stretch = 0)
        # self.addPermanentWidget(self.btn_start)
        # self.addPermanentWidget(self.btn_stop)
        self.addPermanentWidget(self.btn_test1)
        # self.btn_start.clicked.connect(self.on_btn_start)
        # self.btn_stop.clicked.connect(self.on_btn_stop)
        self.btn_test1.clicked.connect(self.on_btn_test1)
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
            # same as self.world.quit()
            self.world.signal_quit()

    @pyqtSlot()
    def on_btn_test1(self):
        # test galaxy parser
        self.world.signal(self.world.SIGNAL_TEST_PARSE_GALAXY, galaxy=1, system=7)
