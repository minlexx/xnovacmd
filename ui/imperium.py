from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QIcon

from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger
from .widget_utils import number_format

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
        def additem_helper(item_texts, align_flag, twi_parent=None):
            # align_flag = Qt::AlignLeft / Qt::AlignRight / Qt::AlignHCenter
            twi = QTreeWidgetItem(item_texts)
            for it_col in range(len(item_texts)):
                if it_col > 0:
                    # void QTreeWidgetItem::setTextAlignment(int column, int alignment)
                    twi.setTextAlignment(it_col, align_flag)
            if twi_parent is None:
                self._tree.addTopLevelItem(twi)
            else:
                twi_parent.addChild(twi)
            return True

        planets = self._world.get_planets()
        header_labels = ['-']
        for i in range(len(planets)):
            # header_labels.append(str(i))
            header_labels.append(planets[i].name)
        header_labels.append('')  # empty last column
        self._tree.setHeaderLabels(header_labels)
        # alignment of text in header labels
        self._tree.header().setDefaultAlignment(Qt.AlignHCenter)
        # default column widths
        for i in range(len(planets)):
            if i < 1:
                self._tree.setColumnWidth(i, 150)
            else:
                self._tree.setColumnWidth(i, 75)
        # names
        item_strings = [self.tr('Name')]
        for pl in planets:
            item_strings.append(pl.name)
        additem_helper(item_strings, Qt.AlignHCenter)
        # coords
        item_strings = [self.tr('Coords')]
        for pl in planets:
            item_strings.append('[{0}:{1}:{2}]'.format(pl.coords.galaxy, pl.coords.system, pl.coords.position))
        additem_helper(item_strings, Qt.AlignHCenter)
        # fields
        item_strings = [self.tr('Fields')]
        for pl in planets:
            item_strings.append('{0}/{1}'.format(pl.fields_busy, pl.fields_total))
        additem_helper(item_strings, Qt.AlignHCenter)
        #
        # resources
        res_root = QTreeWidgetItem([self.tr('Resources')])
        item_strings = [self.tr('Metal')]
        for pl in planets:
            item_strings.append('{0}'.format(number_format(pl.res_current.met)))
        additem_helper(item_strings, Qt.AlignHCenter, res_root)
        item_strings = [self.tr('Crystal')]
        for pl in planets:
            item_strings.append('{0}'.format(number_format(pl.res_current.cry)))
        additem_helper(item_strings, Qt.AlignHCenter, res_root)
        item_strings = [self.tr('Deit')]
        for pl in planets:
            item_strings.append('{0}'.format(number_format(pl.res_current.deit)))
        additem_helper(item_strings, Qt.AlignHCenter, res_root)
        item_strings = [self.tr('Energy')]
        for pl in planets:
            item_strings.append('{0} / {1}'.format(
                number_format(pl.energy.energy_left),
                number_format(pl.energy.energy_total)))
        additem_helper(item_strings, Qt.AlignHCenter, res_root)
        item_strings = [self.tr('Charge')]
        for pl in planets:
            item_strings.append('{0}%'.format(pl.energy.charge_percent))
        additem_helper(item_strings, Qt.AlignHCenter, res_root)
        self._tree.addTopLevelItem(res_root)
        res_root.setExpanded(True)
        #
        # buildings
        buildings_root = QTreeWidgetItem([self.tr('Buildings')])
        item_strings = [self.tr('Metal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_factory))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Crystal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_factory))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Deit factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_factory))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Solar station')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.solar_station))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Nuclear station')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nuclear_station))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Robotics factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.robotics_factory))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Nanites factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nanites_factory))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Shipyard')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.shipyard))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Metal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_silo))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Crystal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_silo))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Deit silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_silo))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Lab')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lab))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('TerraFormer')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.terraformer))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Alliance silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.alliance_silo))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Rocket silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.rocket_silo))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Lunar Base')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_base))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Lunar Phalanx')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_phalanx))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        item_strings = [self.tr('Gates')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.gates))
        additem_helper(item_strings, Qt.AlignHCenter, buildings_root)
        # add/expand
        self._tree.addTopLevelItem(buildings_root)
        buildings_root.setExpanded(True)
        #
        # defense
        defense_root = QTreeWidgetItem([self.tr('Defense')])
        item_strings = [self.tr('Rocket Launcher')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ru))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Light Laser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ll))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Heavy Laser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.tl))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Gauss')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.gauss))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Ion')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.ion))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Plasma')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.plasma))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Small Dome')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.small_dome))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Big Dome')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.big_dome))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Defender Missile')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.defender_rocket))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        item_strings = [self.tr('Attack Missile')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.defense.attack_rocket))
        additem_helper(item_strings, Qt.AlignHCenter, defense_root)
        # add/expand
        self._tree.addTopLevelItem(defense_root)
        defense_root.setExpanded(True)
        #
        # fleet
        fleet_root = QTreeWidgetItem([self.tr('Fleet')])
        item_strings = [self.tr('Small Transport')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.mt))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Big Transport')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.bt))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Light Fighter')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.li))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Heavy Fighter')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.ti))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Cruiser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.crus))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Battleship')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.link))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Colonizer')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.col))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Refiner')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.rab))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Spy')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.spy))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Bomber')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.bomber))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Solar Satellite')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.ss))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Destroyer')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.unik))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Death Star')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.zs))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('BattleCruiser')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.lk))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('War Base')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.warbase))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Corvett')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.f_corvett))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Interceptor')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.f_ceptor))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Dreadnought')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.f_dread))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        item_strings = [self.tr('Corsair')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.ships.f_corsair))
        additem_helper(item_strings, Qt.AlignHCenter, fleet_root)
        # add/expand
        self._tree.addTopLevelItem(fleet_root)
        fleet_root.setExpanded(True)
