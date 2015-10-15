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
        self._tree.addTopLevelItem(res_root)
        res_root.setExpanded(True)
        #
        # buildings
        buildings_root = QTreeWidgetItem([self.tr('Buildings')])
        item_strings = [self.tr('Metal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_factory))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Crystal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_factory))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Deit factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_factory))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Solar station')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.solar_station))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Nuclear station')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nuclear_station))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Robotics factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.robotics_factory))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Nanites factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nanites_factory))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Shipyard')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.shipyard))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Metal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_silo))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Crystal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_silo))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Deit silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_silo))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Lab')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lab))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('TerraFormer')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.terraformer))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Alliance silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.alliance_silo))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Rocket silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.rocket_silo))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Lunar Base')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_base))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Lunar Phalanx')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_phalanx))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Gates')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.gates))
        buildings_root.addChild(QTreeWidgetItem(item_strings))
        self._tree.addTopLevelItem(buildings_root)
        buildings_root.setExpanded(True)
        #
        # defense
        defense_root = QTreeWidgetItem([self.tr('Defense')])
        item_strings = [self.tr('Rocket Launcher')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ru))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Light Laser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ll))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Heavy Laser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.tl))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Gauss')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.gauss))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Ion')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ion))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Plasma')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.plasma))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Small Dome')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.small_dome))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Big Dome')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.big_dome))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Defender Missile')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.defender_rocket))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        item_strings = [self.tr('Attack Missile')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.attack_rocket))
        defense_root.addChild(QTreeWidgetItem(item_strings))
        # add/expand
        self._tree.addTopLevelItem(defense_root)
        defense_root.setExpanded(True)
        #
        # fleet
        fleet_root = QTreeWidgetItem([self.tr('Fleet')])
