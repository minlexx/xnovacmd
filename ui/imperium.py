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
        planets = self._world.get_planets()
        header_labels = ['-']
        for i in range(len(planets)):
            header_labels.append(str(i))
        self._tree.setHeaderLabels(header_labels)
        # default column widths
        for i in range(len(planets)):
            if i < 1:
                self._tree.setColumnWidth(i, 100)
            else:
                self._tree.setColumnWidth(i, 75)
        # names
        item_strings = [self.tr('Name')]
        for pl in planets:
            item_strings.append(pl.name)
        self._tree.addTopLevelItem(QTreeWidgetItem(item_strings))
        # coords
        item_strings = [self.tr('Coords')]
        for pl in planets:
            item_strings.append('[{0}:{1}:{2}]'.format(pl.coords.galaxy, pl.coords.system, pl.coords.position))
        self._tree.addTopLevelItem(QTreeWidgetItem(item_strings))
        # fields
        item_strings = [self.tr('Fields')]
        for pl in planets:
            item_strings.append('{0}/{1}'.format(pl.fields_busy, pl.fields_total))
        self._tree.addTopLevelItem(QTreeWidgetItem(item_strings))
        #
        # resources
        res_root = QTreeWidgetItem([self.tr('Resources')])
        item_strings = [self.tr('Metal')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.res_current.met))
        res_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Crystal')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.res_current.cry))
        res_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Deit')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.res_current.deit))
        res_root.addChild(QTreeWidgetItem(item_strings))
        res_root.setExpanded(True)
        self._tree.addTopLevelItem(res_root)
        #
        buildings_root = QTreeWidgetItem([self.tr('Buildings')])
        defense_root = QTreeWidgetItem([self.tr('Defense')])
        fleet_root = QTreeWidgetItem([self.tr('Fleet')])
