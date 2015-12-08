from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QStatusBar, QPushButton, QProgressBar

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
        # sub-widgets
        self.progressbar = QProgressBar(self)
        self.progressbar.hide()
        self.progressbar.setValue(0)
        self.progressbar.setRange(0, 99)
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

    def set_status(self, msg: str, timeout: int=0):
        self.showMessage(msg, timeout)

    def set_world_load_progress(self, comment: str, progress: int):
        """
        Display world load progress in status bar
        :param comment: string comment of what is currently loading
        :param progress: percent progress, or -1 to disable
        """
        if progress != -1:
            if not self.progressbar.isVisible():
                self.insertPermanentWidget(0, self.progressbar)
                self.progressbar.show()
            msg = self.tr('Loading world') + ' ({0}%) {1}...'.format(progress, comment)
            logger.debug(msg)
            self.progressbar.setValue(progress)
            self.set_status(msg)
        else:
            self.removeWidget(self.progressbar)
            self.progressbar.hide()
            self.progressbar.reset()
            self.clearMessage()

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
