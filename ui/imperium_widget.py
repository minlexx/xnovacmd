from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem
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
        self._layout_topbuttons = None
        self._tree = None
        self._btn_reload = None
        # initialization
        self.setup_ui()

    def setup_ui(self):
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        # create layout for top line of buttons
        self._layout_topbuttons = QHBoxLayout()
        self._layout.addLayout(self._layout_topbuttons)
        # create reload button
        self._btn_reload = QPushButton(self.tr('Refresh imperium'), self)
        self._btn_reload.setIcon(QIcon(':i/reload.png'))
        self._btn_reload.clicked.connect(self.on_btn_refresh_imperium)
        self._layout_topbuttons.addWidget(self._btn_reload)
        # finalize top buttons layout
        self._layout_topbuttons.addStretch()
        # create tree
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

    # called once after full world load
    def update_planets(self):
        def additem_helper(item_texts, twi_parent=None, align_flag=0):
            # align_flag = Qt::AlignLeft / Qt::AlignRight / Qt::AlignHCenter
            if align_flag == 0:
                align_flag = Qt.AlignHCenter | Qt.AlignVCenter
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

        self._tree.clear()  # clear the tree first
        planets = self._world.get_planets()  # get planets from the world
        #
        # setup header and its labels
        header_labels = ['-']
        for i in range(len(planets)):
            header_labels.append(planets[i].name)
        header_labels.append(self.tr('Total'))  # last column - totals
        self._tree.setHeaderLabels(header_labels)
        # alignment of text in header labels
        self._tree.header().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # default column widths
        for i in range(len(planets)):
            if i < 1:
                self._tree.setColumnWidth(i, 150)
            else:
                self._tree.setColumnWidth(i, 75)
        #
        # planets names
        item_strings = [self.tr('Name')]
        for pl in planets:
            item_strings.append(pl.name)
        additem_helper(item_strings)
        #
        # planets coords
        item_strings = [self.tr('Coords')]
        for pl in planets:
            item_strings.append('[{0}:{1}:{2}]'.format(pl.coords.galaxy, pl.coords.system, pl.coords.position))
        additem_helper(item_strings)
        #
        # planets fields
        item_strings = [self.tr('Fields')]
        total_busy = 0
        total_fields = 0
        for pl in planets:
            total_busy += pl.fields_busy
            total_fields = pl.fields_total
            item_strings.append('{0} / {1}'.format(pl.fields_busy, pl.fields_total))
        item_strings.append('{0} / {1}'.format(total_busy, total_fields))
        additem_helper(item_strings)
        #
        # resources
        res_root = QTreeWidgetItem([self.tr('Resources')])
        item_strings = [self.tr('Metal')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_current.met
            item_strings.append('{0}'.format(number_format(pl.res_current.met)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, res_root)
        #
        item_strings = [self.tr('Crystal')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_current.cry
            item_strings.append('{0}'.format(number_format(pl.res_current.cry)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, res_root)
        #
        item_strings = [self.tr('Deit')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_current.deit
            item_strings.append('{0}'.format(number_format(pl.res_current.deit)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, res_root)
        #
        item_strings = [self.tr('Energy')]
        total_busy = 0
        total_fields = 0
        for pl in planets:
            total_busy += pl.energy.energy_left
            total_fields += pl.energy.energy_total
            item_strings.append('{0} / {1}'.format(
                    pl.energy.energy_left,
                    pl.energy.energy_total))
        item_strings.append('{0} / {1}'.format(total_busy, total_fields))
        additem_helper(item_strings, res_root)
        #
        item_strings = [self.tr('Charge')]
        for pl in planets:
            item_strings.append('{0}%'.format(pl.energy.charge_percent))
        additem_helper(item_strings, res_root)
        self._tree.addTopLevelItem(res_root)
        res_root.setExpanded(True)
        #
        # resources per hour
        rph_root = QTreeWidgetItem([self.tr('Production')])
        item_strings = [self.tr('Met/h')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_per_hour.met
            item_strings.append('{0}'.format(number_format(pl.res_per_hour.met)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, rph_root)
        #
        item_strings = [self.tr('Cry/h')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_per_hour.cry
            item_strings.append('{0}'.format(number_format(pl.res_per_hour.cry)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, rph_root)
        #
        item_strings = [self.tr('Deit/h')]
        total_res = 0
        for pl in planets:
            total_res += pl.res_per_hour.deit
            item_strings.append('{0}'.format(number_format(pl.res_per_hour.deit)))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, rph_root)
        self._tree.addTopLevelItem(rph_root)
        rph_root.setExpanded(True)
        #
        # buildings
        buildings_root = QTreeWidgetItem([self.tr('Buildings')])
        item_strings = [self.tr('Metal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_factory))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Crystal factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_factory))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Deit factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_factory))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Solar station')]
        for pl in planets:
            # testing: detect solar station level up
            addstr = '{0}'.format(pl.buildings.solar_station)
            if pl.is_build_in_progress('Солнечная батарея'):
                addstr = '{0} -> {1}'.format(pl.buildings.solar_station, pl.buildings.solar_station+1)
            item_strings.append(addstr)
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Nuclear station')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nuclear_station))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Robotics factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.robotics_factory))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Nanites factory')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.nanites_factory))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Shipyard')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.shipyard))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Metal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.met_silo))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Crystal silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.cry_silo))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Deit silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.deit_silo))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Lab')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lab))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('TerraFormer')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.terraformer))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Alliance silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.alliance_silo))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Rocket silo')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.rocket_silo))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Lunar Base')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_base))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Lunar Phalanx')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.lunar_phalanx))
        additem_helper(item_strings, buildings_root)
        item_strings = [self.tr('Gates')]
        for pl in planets:
            item_strings.append('{0}'.format(pl.buildings.gates))
        additem_helper(item_strings, buildings_root)
        # add/expand
        self._tree.addTopLevelItem(buildings_root)
        buildings_root.setExpanded(True)
        #
        # defense
        defense_root = QTreeWidgetItem([self.tr('Defense')])
        item_strings = [self.tr('Rocket Launcher')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.ru
            item_strings.append(number_format(pl.defense.ru))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Light Laser')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.ll
            item_strings.append(number_format(pl.defense.ll))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Heavy Laser')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.tl
            item_strings.append(number_format(pl.defense.tl))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Gauss')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.gauss
            item_strings.append(number_format(pl.defense.gauss))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Ion')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.ion
            item_strings.append(number_format(pl.defense.ion))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Plasma')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.plasma
            item_strings.append(number_format(pl.defense.plasma))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Small Dome')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.small_dome
            item_strings.append(number_format(pl.defense.small_dome))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Big Dome')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.big_dome
            item_strings.append(number_format(pl.defense.big_dome))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Defender Missile')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.defender_rocket
            item_strings.append(number_format(pl.defense.defender_rocket))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        #
        item_strings = [self.tr('Attack Missile')]
        total_res = 0
        for pl in planets:
            total_res += pl.defense.attack_rocket
            item_strings.append(number_format(pl.defense.attack_rocket))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, defense_root)
        # add/expand
        self._tree.addTopLevelItem(defense_root)
        defense_root.setExpanded(True)
        #
        # fleet
        fleet_root = QTreeWidgetItem([self.tr('Fleet')])
        item_strings = [self.tr('Small Transport')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.mt
            item_strings.append(number_format(pl.ships.mt))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Big Transport')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.bt
            item_strings.append(number_format(pl.ships.bt))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Light Fighter')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.li
            item_strings.append(number_format(pl.ships.li))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Heavy Fighter')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.ti
            item_strings.append(number_format(pl.ships.ti))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Cruiser')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.crus
            item_strings.append(number_format(pl.ships.crus))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Battleship')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.link
            item_strings.append(number_format(pl.ships.link))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Colonizer')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.col
            item_strings.append(number_format(pl.ships.col))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Refiner')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.rab
            item_strings.append(number_format(pl.ships.rab))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Spy')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.spy
            item_strings.append(number_format(pl.ships.spy))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Bomber')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.bomber
            item_strings.append(number_format(pl.ships.bomber))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Solar Satellite')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.ss
            item_strings.append(number_format(pl.ships.ss))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Destroyer')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.unik
            item_strings.append(number_format(pl.ships.unik))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Death Star')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.zs
            item_strings.append(number_format(pl.ships.zs))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('BattleCruiser')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.lk
            item_strings.append(number_format(pl.ships.lk))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('War Base')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.warbase
            item_strings.append(number_format(pl.ships.warbase))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Corvett')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.f_corvett
            item_strings.append(number_format(pl.ships.f_corvett))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Interceptor')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.f_ceptor
            item_strings.append(number_format(pl.ships.f_ceptor))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Dreadnought')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.f_dread
            item_strings.append(number_format(pl.ships.f_dread))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        #
        item_strings = [self.tr('Corsair')]
        total_res = 0
        for pl in planets:
            total_res += pl.ships.f_corsair
            item_strings.append(number_format(pl.ships.f_corsair))
        item_strings.append(number_format(total_res))
        additem_helper(item_strings, fleet_root)
        # add/expand
        self._tree.addTopLevelItem(fleet_root)
        fleet_root.setExpanded(True)

    def update_planet_resources(self):
        res_top_twi = self._tree.topLevelItem(3)  # 4th top level item is "Resources"
        if res_top_twi is None:
            return
        res_met_twi = res_top_twi.child(0)   # first child is metal
        res_cry_twi = res_top_twi.child(1)   # 2nd is crystal
        res_deit_twi = res_top_twi.child(2)  # 3rd is deit
        res_en_twi = res_top_twi.child(3)    # 4th is energy
        if (res_met_twi is None) or (res_cry_twi is None) or (res_deit_twi is None) \
                or (res_en_twi is None):
            return
        planets = self._world.get_planets()  # get planets from the world
        ncolumn = 1  # column #0 is description, planets start at #1
        totals = [0, 0, 0]  # count total resources
        for planet in planets:
            res_met_twi.setText(ncolumn, number_format(int(planet.res_current.met)))
            res_cry_twi.setText(ncolumn, number_format(int(planet.res_current.cry)))
            res_deit_twi.setText(ncolumn, number_format(int(planet.res_current.deit)))
            res_en_twi.setText(ncolumn, '{0} / {1}'.format(
                planet.energy.energy_left, planet.energy.energy_total))
            ncolumn += 1
            totals[0] += int(planet.res_current.met)
            totals[1] += int(planet.res_current.cry)
            totals[2] += int(planet.res_current.deit)
        # set values for "totals" column
        res_met_twi.setText(ncolumn, number_format(totals[0]))
        res_cry_twi.setText(ncolumn, number_format(totals[1]))
        res_deit_twi.setText(ncolumn, number_format(totals[2]))

    @pyqtSlot()
    def on_btn_refresh_imperium(self):
        logger.debug('refresh imperium clicked')
        self._world.signal(self._world.SIGNAL_RELOAD_PAGE, page_name='imperium')
