from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QIcon

from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger
logger = xn_logger.get(__name__, debug=True)


class ImperiumWidget(QWidget):
    def __init__(self, parent=None):
        super(ImperiumWidget, self).__init__(parent)
        # objects, sub-windows
        self._world = XNovaWorld_instance()
        self._layout = None
        self._tree = None
        # initialization
        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self._tree = QTreeWidget(self)
        self._tree.setAnimated(False)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setHeaderHidden(False)
        self._tree.setItemsExpandable(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSortingEnabled(False)
        self._tree.setColumnCount(1)
        self._tree.setHeaderLabels(['None'])
        self._layout.addWidget(self._tree)
        self._tree.show()

    def update_planets(self):
        pass
