from PyQt5.QtWidgets import QStatusBar, QPushButton, QProgressBar, QLabel

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
        # progressbar
        self._progressbar = QProgressBar(self)
        self._progressbar.hide()
        self._progressbar.setValue(0)
        self._progressbar.setRange(0, 99)
        # online players counter
        self._lbl_online = QLabel(self.tr('Online') + ': 0', self)
        # testing only
        # self._btn_test1 = QPushButton(self.tr('test parse'), self)
        # self.addPermanentWidget(self._btn_test1)
        # self._btn_test1.clicked.connect(self.on_btn_test1)
        #
        self.addPermanentWidget(self._lbl_online)  # should be las right widget
        self.show()

    def set_status(self, msg: str, timeout: int=0):
        self.showMessage(msg, timeout)

    def set_world_load_progress(self, comment: str, progress: int):
        """
        Display world load progress in status bar
        :param comment: string comment of what is currently loading
        :param progress: percent progress, or -1 to disable
        """
        if progress != -1:
            if not self._progressbar.isVisible():
                self.insertPermanentWidget(0, self._progressbar)
                self._progressbar.show()
            msg = self.tr('Loading world') + ' ({0}%) {1}...'.format(progress, comment)
            logger.debug(msg)
            self._progressbar.setValue(progress)
            self.set_status(msg)
        else:
            self.removeWidget(self._progressbar)
            self._progressbar.hide()
            self._progressbar.reset()
            self.clearMessage()

    def update_online_players_count(self):
        op = self.world.get_online_players()
        self._lbl_online.setText(self.tr('Online') + ': {0}'.format(op))

# some functions may be useful, documentation:
# void QStatusBar::clearMessage()
# void QStatusBar::addPermanentWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::addWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::removeWidget(QWidget * widget)

    #@pyqtSlot()
    #def on_btn_test1(self):
    #    # test galaxy parser
    #    self.world.signal(self.world.SIGNAL_TEST_PARSE_GALAXY, galaxy=1, system=7)
