from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QVariant, QTimer
from PyQt5.QtWidgets import QWidget, QFrame, QMenu, QAction, \
    QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QToolButton, \
    QMessageBox, QGridLayout, QScrollArea, QLayout
from PyQt5.QtGui import QIcon, QCursor, QPixmap, QFont

from ui.xnova.xn_data import XNPlanet, XNCoords, XNPlanetBuildingItem, XNResourceBundle
from ui.xnova.xn_world import XNovaWorld_instance, XNovaWorld
from ui.xnova import xn_logger

from ui.customwidgets.collapsible_frame import CollapsibleFrame
from ui.customwidgets.input_string_dialog import input_string_dialog

from ui.widget_utils import number_format, time_seconds_to_str

logger = xn_logger.get(__name__, debug=True)


class Planet_BasicInfoPanel(QFrame):

    requestOpenGalaxy = pyqtSignal(XNCoords)
    requestRefreshPlanet = pyqtSignal()
    requestRenamePlanet = pyqtSignal(int, str)   # planet_id, new_planet_name

    def __init__(self, parent: QWidget):
        super(Planet_BasicInfoPanel, self).__init__(parent)
        #
        self._planet_pic_url = ''
        self._pixmap = QPixmap()
        self._planet = XNPlanet()
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # bold font
        font = self.font()
        font.setWeight(QFont.Bold)
        # layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)
        self._vlayout = QVBoxLayout()
        self._hlayout_name_coords = QHBoxLayout()
        self._hlayout_fields = QHBoxLayout()
        self._hlayout_res = QHBoxLayout()
        self._hlayout_energy = QHBoxLayout()
        # labels
        self._lbl_img = QLabel(self)
        self._lbl_name = QLabel(self)
        self._lbl_coords = QLabel(self)
        self._lbl_coords.linkActivated.connect(self.on_coords_link_activated)
        self._lbl_fields = QLabel()
        # resource labels
        self._lbl_metal = QLabel(self.tr('Metal:'), self)
        self._lbl_crystal = QLabel(self.tr('Crystal:'), self)
        self._lbl_deit = QLabel(self.tr('Deiterium:'), self)
        self._lbl_cur_met = QLabel(self)
        self._lbl_cur_cry = QLabel(self)
        self._lbl_cur_deit = QLabel(self)
        self._lbl_cur_met.setFont(font)
        self._lbl_cur_cry.setFont(font)
        self._lbl_cur_deit.setFont(font)
        # energy labels
        self._lbl_energy = QLabel(self.tr('Energy, charge:'), self)
        self._lbl_energy_stats = QLabel(self)
        self._lbl_energy_stats.setFont(font)
        # button
        self._btn_refresh = QPushButton(self.tr('Refresh planet'), self)
        self._btn_refresh.setIcon(QIcon(':/i/reload.png'))
        self._btn_refresh.clicked.connect(self.on_btn_refresh_clicked)
        self._btn_tools = QToolButton(self)
        self._btn_tools.setIcon(QIcon(':/i/tools_32.png'))
        self._btn_tools.setText(self.tr('Actions...'))
        self._btn_tools.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._btn_tools.setPopupMode(QToolButton.InstantPopup)
        self._actions_menu = QMenu(self)
        self._action_renameplanet = QAction(self.tr('Rename planet'), self)
        self._action_leaveplanet = QAction(self.tr('Leave planet'), self)
        self._actions_menu.addAction(self._action_renameplanet)
        self._actions_menu.addAction(self._action_leaveplanet)
        self._btn_tools.setMenu(self._actions_menu)
        self._action_renameplanet.triggered.connect(self.on_action_renameplanet)
        self._action_leaveplanet.triggered.connect(self.on_action_leaveplanet)
        # finalize layout
        self._hlayout_name_coords.addWidget(self._lbl_name)
        self._hlayout_name_coords.addWidget(self._lbl_coords)
        self._hlayout_name_coords.addWidget(self._btn_refresh)
        self._hlayout_name_coords.addWidget(self._btn_tools)
        self._hlayout_name_coords.addStretch()
        self._hlayout_fields.addWidget(self._lbl_fields)
        self._hlayout_fields.addStretch()
        self._hlayout_res.addWidget(self._lbl_metal)
        self._hlayout_res.addWidget(self._lbl_cur_met)
        self._hlayout_res.addWidget(self._lbl_crystal)
        self._hlayout_res.addWidget(self._lbl_cur_cry)
        self._hlayout_res.addWidget(self._lbl_deit)
        self._hlayout_res.addWidget(self._lbl_cur_deit)
        self._hlayout_res.addStretch()
        self._hlayout_energy.addWidget(self._lbl_energy)
        self._hlayout_energy.addWidget(self._lbl_energy_stats)
        self._hlayout_energy.addStretch()
        #
        self._vlayout.addLayout(self._hlayout_name_coords)
        self._vlayout.addLayout(self._hlayout_fields)
        self._vlayout.addLayout(self._hlayout_res)
        self._vlayout.addLayout(self._hlayout_energy)
        self._vlayout.addStretch()
        self._layout.addWidget(self._lbl_img)
        self._layout.addLayout(self._vlayout)
        self._layout.addStretch()
        #
        # setup timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.on_timer)

    def setup_from_planet(self, planet: XNPlanet):
        # store references
        self._planet = planet
        self._planet_pic_url = planet.pic_url
        # deal with planet pic
        file_name = './cache/img/{0}'.format(self._planet_pic_url.replace('/', '_'))
        self._pixmap = QPixmap(file_name)
        self._lbl_img.setPixmap(self._pixmap)
        # setup widget max height based on picture size and layout's margins
        margins = self._layout.contentsMargins()
        top_margin = margins.top()
        bottom_margin = margins.bottom()
        self.setMaximumHeight(self._pixmap.height() + top_margin + bottom_margin)
        # planet name, corods, fields
        self._lbl_name.setText(planet.name)
        self._lbl_coords.setText('<a href="{0}">{0}</a>'.format(planet.coords.coords_str()))
        fields_left_str = '{0}: {1}'.format(self.tr('left'), planet.fields_total - planet.fields_busy)
        self._lbl_fields.setText(self.tr('Fields:') +
                                 ' {0} / {1} ({2})'.format(planet.fields_busy,
                                                           planet.fields_total,
                                                           fields_left_str))
        # resources
        self._set_resources()
        # restart timer
        self._timer.stop()
        self._timer.setInterval(1000)
        self._timer.setSingleShot(False)
        self._timer.start()

    def _set_resources(self):
        # update planet resources
        self._lbl_cur_met.setText(number_format(int(self._planet.res_current.met)))
        self._lbl_cur_cry.setText(number_format(int(self._planet.res_current.cry)))
        self._lbl_cur_deit.setText(number_format(int(self._planet.res_current.deit)))
        # energy
        self._lbl_energy_stats.setText('{0} / {1}    ({2}%)'.format(
                self._planet.energy.energy_left,
                self._planet.energy.energy_total,
                self._planet.energy.charge_percent))

    @pyqtSlot(str)
    def on_coords_link_activated(self, link: str):
        coords = XNCoords()
        coords.parse_str(link, raise_on_error=True)
        self.requestOpenGalaxy.emit(coords)

    @pyqtSlot()
    def on_btn_refresh_clicked(self):
        self.requestRefreshPlanet.emit()

    @pyqtSlot()
    def on_timer(self):
        self._set_resources()

    @pyqtSlot()
    def on_action_renameplanet(self):
        new_name = input_string_dialog(
                self,
                self.tr('Rename planet'),
                self.tr('Enter new planet name:'),
                self._planet.name)
        if (new_name is not None) and (new_name != self._planet.name):
            self.requestRenamePlanet.emit(self._planet.planet_id, new_name)

    @pyqtSlot()
    def on_action_leaveplanet(self):
        QMessageBox.warning(self, self.tr('Not done'),
                            self.tr('Leaving planet is not done!'))


class Planet_BuildItemWidget(QFrame):
    def __init__(self, parent: QWidget):
        super(Planet_BuildItemWidget, self).__init__(parent)
        # data members
        self._bitem = XNPlanetBuildingItem()
        self._pix = QPixmap()
        self._pix_met = QPixmap(':/i/s_metall.png')
        self._pix_cry = QPixmap(':/i/s_kristall.png')
        self._pix_deit = QPixmap(':/i/s_deuterium.png')
        self._pix_energy = QPixmap(':/i/s_energy.png')
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # font
        font = self.font()
        font.setWeight(QFont.Bold)
        # layout
        self._layout = QHBoxLayout()
        self._layout_v = QVBoxLayout()
        self.setLayout(self._layout)
        # label with building image
        self._lbl_pix = QLabel(self)
        # labels for name and level
        self._layout_nl = QHBoxLayout()
        self._lbl_name = QLabel(self)
        self._lbl_name.setFont(font)
        self._lbl_lvl = QLabel(self)
        # labels for time
        self._layout_buildtime = QHBoxLayout()
        self._lbl_time = QLabel(self.tr('Time:'), self)
        self._lbl_timestr = QLabel(self)
        # labels for price
        self._layout_price1 = QHBoxLayout()
        self._layout_price2 = QHBoxLayout()
        self._layout_price3 = QHBoxLayout()
        self._layout_price4 = QHBoxLayout()
        self._lbl_price_met_ico = QLabel(self)
        self._lbl_price_met_ico.setPixmap(self._pix_met)
        self._lbl_price_met = QLabel()
        self._lbl_price_cry_ico = QLabel()
        self._lbl_price_cry_ico.setPixmap(self._pix_cry)
        self._lbl_price_cry = QLabel()
        self._lbl_price_deit_ico = QLabel()
        self._lbl_price_deit_ico.setPixmap(self._pix_deit)
        self._lbl_price_deit = QLabel()
        self._lbl_price_energy_ico = QLabel()
        self._lbl_price_energy_ico.setPixmap(self._pix_energy)
        self._lbl_price_energy = QLabel()
        # buttons
        self._layout_buttons = QHBoxLayout()
        self._btn_upgrade = QPushButton(self.tr('Upgrade'), self)
        self._btn_upgrade.setIcon(QIcon(':/i/build.png'))
        self._btn_upgrade.setMaximumHeight(25)
        # construct layout
        # name, level
        self._layout_nl.addWidget(self._lbl_name)
        self._layout_nl.addWidget(self._lbl_lvl)
        self._layout_nl.addStretch()
        self._layout_v.addLayout(self._layout_nl)
        # build time
        self._layout_buildtime.addWidget(self._lbl_time)
        self._layout_buildtime.addWidget(self._lbl_timestr)
        self._layout_buildtime.addStretch()
        self._layout_v.addLayout(self._layout_buildtime)
        # price met
        self._layout_price1.addWidget(self._lbl_price_met_ico)
        self._layout_price1.addWidget(self._lbl_price_met)
        self._layout_price1.addStretch()
        # price cry
        self._layout_price2.addWidget(self._lbl_price_cry_ico)
        self._layout_price2.addWidget(self._lbl_price_cry)
        self._layout_price2.addStretch()
        # price deit
        self._layout_price3.addWidget(self._lbl_price_deit_ico)
        self._layout_price3.addWidget(self._lbl_price_deit)
        self._layout_price3.addStretch()
        # price energy
        self._layout_price4.addWidget(self._lbl_price_energy_ico)
        self._layout_price4.addWidget(self._lbl_price_energy)
        self._layout_price4.addStretch()
        self._layout_v.addLayout(self._layout_price1)
        self._layout_v.addLayout(self._layout_price2)
        self._layout_v.addLayout(self._layout_price3)
        self._layout_v.addLayout(self._layout_price4)
        # buttons
        self._layout_buttons.addWidget(self._btn_upgrade)
        self._layout_buttons.addStretch()
        self._layout_v.addLayout(self._layout_buttons)
        #
        self._layout.addWidget(self._lbl_pix, 0, Qt.AlignTop | Qt.AlignHCenter)
        self._layout.addLayout(self._layout_v)

    def set_building_item(self, bitem: XNPlanetBuildingItem, res_cur: XNResourceBundle, energy_cur: int):
        self._bitem = bitem
        # load pixmap
        pix_fn = 'ui/i/building_{0}.gif'.format(bitem.gid)
        if not self._pix.load(pix_fn):
            logger.warn('Failed to load pixmap from: [{0}]'.format(pix_fn))
        else:
            self._lbl_pix.setPixmap(self._pix.scaled(80, 80))
            # self._lbl_pix.setPixmap(self._pix)
        # name, level
        self._lbl_name.setText(bitem.name)
        self._lbl_lvl.setText(str(bitem.level))
        # time
        if bitem.seconds_total != -1:
            self._lbl_timestr.setText(time_seconds_to_str(bitem.seconds_total))
        else:
            self._lbl_timestr.setText('-')
        # colors
        color_enough = '#008800'
        color_notenough = '#AA0000'
        enough_met = True
        enough_cry = True
        enough_deit = True
        enough_energy = True
        # price met
        setstr = ''
        if bitem.cost_met > 0:
            setstr = number_format(bitem.cost_met)
            color = color_enough
            if res_cur.met < bitem.cost_met:
                setstr += ' (-{0})'.format(number_format(int(bitem.cost_met - res_cur.met)))
                color = color_notenough
                enough_met = False
            self._lbl_price_met.setText('<font color="{0}">{1}</font>'.format(color, setstr))
            self._lbl_price_met_ico.show()
            self._lbl_price_met.show()
        else:
            self._lbl_price_met_ico.hide()
            self._lbl_price_met.hide()
        # price cry
        setstr = ''
        if bitem.cost_cry > 0:
            setstr = number_format(bitem.cost_cry)
            color = color_enough
            if res_cur.cry < bitem.cost_cry:
                setstr += ' (-{0})'.format(number_format(int(bitem.cost_cry - res_cur.cry)))
                color = color_notenough
                enough_cry = False
            self._lbl_price_cry.setText('<font color="{0}">{1}</font>'.format(color, setstr))
            self._lbl_price_cry_ico.show()
            self._lbl_price_cry.show()
        else:
            self._lbl_price_cry_ico.hide()
            self._lbl_price_cry.hide()
        # price deit
        setstr = ''
        if bitem.cost_deit > 0:
            setstr = number_format(bitem.cost_deit)
            color = color_enough
            enough_deit = False
            if res_cur.deit < bitem.cost_deit:
                setstr += ' (-{0})'.format(number_format(int(bitem.cost_deit - res_cur.deit)))
                color = color_notenough
            self._lbl_price_deit.setText('<font color="{0}">{1}</font>'.format(color, setstr))
            self._lbl_price_deit_ico.show()
            self._lbl_price_deit.show()
        else:
            self._lbl_price_deit_ico.hide()
            self._lbl_price_deit.hide()
        # price energy
        setstr = ''
        if bitem.cost_energy > 0:
            setstr = number_format(bitem.cost_energy)
            color = color_enough
            if energy_cur < bitem.cost_energy:
                setstr += ' (-{0})'.format(number_format(int(bitem.cost_energy - energy_cur)))
                color = color_notenough
                enough_energy = False
            self._lbl_price_energy.setText('<font color="{0}">{1}</font>'.format(color, setstr))
            self._lbl_price_energy_ico.show()
            self._lbl_price_energy.show()
        else:
            self._lbl_price_energy_ico.hide()
            self._lbl_price_energy.hide()
        # enable or disable buttons
        if enough_met and enough_cry and enough_deit and enough_energy:
            self._btn_upgrade.setEnabled(True)
        else:
            self._btn_upgrade.setEnabled(False)


class Planet_BuildItemsPanel(QFrame):

    TYPE_BUILDINGS = 'buildings'
    TYPE_SHIPYARD = 'shipyard'
    TYPE_RESEARCHES = 'researches'

    def __init__(self, parent: QWidget):
        super(Planet_BuildItemsPanel, self).__init__(parent)
        # data members
        self._type = ''
        self._planet = XNPlanet()
        # setup frame
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)
        # layout
        self._layout = QGridLayout()
        self._layout_lastcol = 0
        self._layout_lastrow = 0
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(3)
        self._layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(self._layout)
        #
        # build item widgets
        self._biws = dict()
        # "constants"
        self.MAX_COLS = 3

    def get_type(self) -> str:
        return self._type

    def get_planet(self) -> XNPlanet:
        return self._planet

    def set_type(self, typ: str):
        # cannot set type twice
        if self._type != '':
            raise ValueError('Planet_BuildItemsPanel: Cannot set type twice!')
        if typ not in [self.TYPE_BUILDINGS, self.TYPE_SHIPYARD, self.TYPE_RESEARCHES]:
            raise ValueError('Planet_BuildItemsPanel: invalid type: [{0}]!'.format(typ))
        self._type = typ

    def set_planet(self, planet: XNPlanet):
        self._planet = planet
        # update info in widgets
        if self._type == self.TYPE_BUILDINGS:
            for bitem in self._planet.buildings_items:
                biw = self.biw_for_gid(bitem.gid)
                biw.set_building_item(bitem, self._planet.res_current, self._planet.energy.energy_total)
                biw.show()
        elif self._type == self.TYPE_SHIPYARD:
            for bitem in self._planet.shipyard_tems:
                biw = self.biw_for_gid(bitem.gid)
                biw.set_building_item(bitem, self._planet.res_current, self._planet.energy.energy_total)
                biw.show()
        elif self._type == self.TYPE_RESEARCHES:
            for bitem in self._planet.research_items:
                biw = self.biw_for_gid(bitem.gid)
                biw.set_building_item(bitem, self._planet.res_current, self._planet.energy.energy_total)
                biw.show()
            for bitem in self._planet.researchfleet_items:
                biw = self.biw_for_gid(bitem.gid)
                biw.set_building_item(bitem, self._planet.res_current, self._planet.energy.energy_total)
                biw.show()

    def biw_for_gid(self, gid: int) -> Planet_BuildItemWidget:
        """
        Gets existing child widget for build item, or creates it
        :param gid: building id
        :return: Planet_BuildItemWidget
        """
        if gid not in self._biws:
            biw = Planet_BuildItemWidget(self)
            biw.hide()
            self._biws[gid] = biw
            self._layout.addWidget(biw, self._layout_lastrow, self._layout_lastcol)
            self._layout_lastcol += 1
            if self._layout_lastcol > (self.MAX_COLS -1):
                self._layout_lastcol = 0
                self._layout_lastrow += 1
        else:
            biw = self._biws[gid]
        return biw


class PlanetWidget(QFrame):
    """
    Provides view of galaxy/solarsystem contents as table widget
    """

    requestOpenGalaxy = pyqtSignal(XNCoords)

    def __init__(self, parent: QWidget):
        super(PlanetWidget, self).__init__(parent)
        #
        self.world = XNovaWorld_instance()
        self._planet = XNPlanet()
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(3)
        self.setLayout(self._layout)
        # basic info panel
        self._bipanel = Planet_BasicInfoPanel(self)
        self._bipanel.requestOpenGalaxy.connect(self.on_request_open_galaxy)
        self._bipanel.requestRefreshPlanet.connect(self.on_request_refresh_planet)
        self._bipanel.requestRenamePlanet.connect(self.on_request_rename_planet)
        # buildings
        self._cf_buildings = CollapsibleFrame(self)
        self._cf_buildings.setTitle(self.tr('Buildings'))
        self._sa_buildings = QScrollArea(self._cf_buildings)
        self._bip_buildings = Planet_BuildItemsPanel(self._sa_buildings)
        self._bip_buildings.set_type(Planet_BuildItemsPanel.TYPE_BUILDINGS)
        self._bip_buildings.show()
        self._sa_buildings.setWidget(self._bip_buildings)
        self._cf_buildings.addWidget(self._sa_buildings)
        # shipyard
        self._cf_shipyard = CollapsibleFrame(self)
        self._cf_shipyard.setTitle(self.tr('Shipyard'))
        self._sa_shipyard = QScrollArea(self._cf_shipyard)
        self._bip_shipyard = Planet_BuildItemsPanel(self._cf_shipyard)
        self._bip_shipyard.set_type(Planet_BuildItemsPanel.TYPE_SHIPYARD)
        self._sa_shipyard.setWidget(self._bip_shipyard)
        self._cf_shipyard.addWidget(self._sa_shipyard)
        # research
        self._cf_research = CollapsibleFrame(self)
        self._cf_research.setTitle(self.tr('Research'))
        self._sa_research = QScrollArea(self._cf_research)
        self._bip_research = Planet_BuildItemsPanel(self._cf_research)
        self._bip_research.set_type(Planet_BuildItemsPanel.TYPE_RESEARCHES)
        self._sa_research.setWidget(self._bip_research)
        self._cf_research.addWidget(self._sa_research)
        # layout finalize
        self._layout.addWidget(self._bipanel)
        self._layout.addWidget(self._cf_buildings)
        self._layout.addWidget(self._cf_shipyard)
        self._layout.addWidget(self._cf_research)
        # expand buildings frame by default
        self._cf_buildings.expand()
        #
        # connect signals
        self._cf_buildings.expanded.connect(self.on_frame_buildings_expanded)
        self._cf_buildings.collapsed.connect(self.on_frame_buildings_collapsed)
        self._cf_shipyard.expanded.connect(self.on_frame_shipyard_expanded)
        self._cf_shipyard.collapsed.connect(self.on_frame_shipyard_collapsed)
        self._cf_research.expanded.connect(self.on_frame_research_expanded)
        self._cf_research.collapsed.connect(self.on_frame_research_collapsed)

    def get_tab_type(self) -> str:
        return 'planet'

    def setPlanet(self, planet: XNPlanet):
        self._planet = planet
        self._bipanel.setup_from_planet(self._planet)
        self._bip_buildings.set_planet(planet)
        self._bip_shipyard.set_planet(planet)
        self._bip_research.set_planet(planet)

    def planet(self) -> XNPlanet:
        return self._planet

    @pyqtSlot(XNCoords)
    def on_request_open_galaxy(self, coords: XNCoords):
        self.requestOpenGalaxy.emit(coords)

    @pyqtSlot()
    def on_request_refresh_planet(self):
        self.world.signal(self.world.SIGNAL_RELOAD_PLANET, planet_id=self._planet.planet_id)

    @pyqtSlot(int, str)
    def on_request_rename_planet(self, planet_id: int, planet_name: str):
        self.world.signal(self.world.SIGNAL_RENAME_PLANET, planet_id=planet_id, new_name=planet_name)

    @pyqtSlot()
    def on_frame_buildings_collapsed(self):
        pass

    @pyqtSlot()
    def on_frame_buildings_expanded(self):
        # collapse other frames
        self._cf_shipyard.collapse()
        self._cf_research.collapse()

    @pyqtSlot()
    def on_frame_shipyard_collapsed(self):
        pass

    @pyqtSlot()
    def on_frame_shipyard_expanded(self):
        # collapse other frames
        self._cf_buildings.collapse()
        self._cf_research.collapse()

    @pyqtSlot()
    def on_frame_research_collapsed(self):
        pass

    @pyqtSlot()
    def on_frame_research_expanded(self):
        # collapse other frames
        self._cf_buildings.collapse()
        self._cf_shipyard.collapse()
