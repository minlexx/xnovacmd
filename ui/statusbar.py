from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QStatusBar
from PyQt5.QtGui import QIcon

from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class XNCStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super(XNCStatusBar, self).__init__(parent)
        # state vars
        # initialization
        self.setupUi()

    def setupUi(self):
        self.setSizeGripEnabled(True)
        self.show()
        self.showMessage('wow')

    def setStatus(self, msg: str, timeout: int=0):
        self.showMessage(msg, timeout)

# some functions may be useful, documentation:
# void QStatusBar::clearMessage()
# void QStatusBar::addPermanentWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::addWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::removeWidget(QWidget * widget)

