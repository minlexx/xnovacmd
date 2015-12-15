from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot, QRect
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QVBoxLayout, \
    QHBoxLayout, QGroupBox, QLabel, QProgressBar
from PyQt5.QtGui import QIcon, QFont

from .xnova.xn_data import fraction_from_name, XNAccountInfo, XNPlanet, XNPlanetBuildingItem
from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger

from .widget_utils import number_format

logger = xn_logger.get(__name__, debug=True)


BPW_TYPE_SHIPYARD = 'shipyard'
BPW_TYPE_RESEARCH = 'research'


class  Overview_AccStatsWidget(QWidget):
    def __init__(self, parent=None):
        super(Overview_AccStatsWidget, self).__init__(parent)
        self.ui = None

    def load_ui(self):
        self.ui = uic.loadUi('ui/overview_accstats.ui', self)
        self.ui.gb_account.setTitle(self.tr('Player:'))
        # stats columns widths
        self.ui.tw_accStats.setColumnWidth(0, 130)
        self.ui.tw_accStats.setColumnWidth(1, 300)
        # init translatable table rows values in 1st column
        self.set_as_item(0, 0, self.tr('Buildings:'))
        self.set_as_item(1, 0, self.tr('Fleet:'))
        self.set_as_item(2, 0, self.tr('Defense:'))
        self.set_as_item(3, 0, self.tr('Science:'))
        self.set_as_item(4, 0, self.tr('Total:'))
        self.set_as_item(5, 0, self.tr('Industry:'))
        self.set_as_item(6, 0, self.tr('Military:'))
        self.set_as_item(7, 0, self.tr('Wins/Losses:'))
        self.set_as_item(8, 0, self.tr('Credits:'))
        self.set_as_item(9, 0, self.tr('Fraction:'))
        self.set_as_item(10, 0, self.tr('Alliance:'))

    def set_as_item(self, row: int, col: int, text):
        twi = QTableWidgetItem(str(text))
        self.ui.tw_accStats.setItem(row, col, twi)

    def update_account_info(self, a: XNAccountInfo):
        # a = self.world.get_account_info()
        self.ui.gb_account.setTitle(self.tr('Player: {0} (id={1})').format(a.login, a.id))
        self.set_as_item(0, 1, self.tr('{0} rank {1}').format(
            number_format(a.scores.buildings), a.scores.buildings_rank))
        self.set_as_item(1, 1, self.tr('{0} rank {1}').format(
            number_format(a.scores.fleet), a.scores.fleet_rank))
        self.set_as_item(2, 1, self.tr('{0} rank {1}').format(
            number_format(a.scores.defense), a.scores.defense_rank))
        self.set_as_item(3, 1, self.tr('{0} rank {1}').format(
            number_format(a.scores.science), a.scores.science_rank))
        # total: 15156 rank 195 (+2)
        rank_delta_str = '+' + str(a.scores.rank_delta)  # explicit "+" sign
        if a.scores.rank_delta < 0:
            rank_delta_str = str(a.scores.rank_delta)
        self.set_as_item(4, 1, self.tr('{0} rank {1} ({2})').format(
            number_format(a.scores.total), a.scores.rank, rank_delta_str))
        self.set_as_item(5, 1, self.tr('{0} lv ({1}/{2} exp)').format(
            a.scores.industry_level, a.scores.industry_exp[0], a.scores.industry_exp[1]))
        self.set_as_item(6, 1, self.tr('{0} lv ({1}/{2} exp)').format(
            a.scores.military_level, a.scores.military_exp[0], a.scores.military_exp[1]))
        self.set_as_item(7, 1, self.tr('{0} W / {1} L').format(a.scores.wins, a.scores.losses))
        self.set_as_item(8, 1, a.scores.credits)
        self.set_as_item(10, 1, a.alliance_name)
        # fraction
        fr = fraction_from_name(a.scores.fraction)
        if fr:
            icon = QIcon(':/i/{0}'.format(fr.ico_name))
            twi = QTableWidgetItem(icon, str(a.scores.fraction))
            self.ui.tw_accStats.setItem(9, 1, twi)


class Overview_BuildProgressWidget(QWidget):
    def __init__(self, parent=None):
        super(Overview_BuildProgressWidget, self).__init__(parent)
        self.planet = None
        self.building_item = None
        self.is_shipyard = False
        self.is_research = False
        self.load_ui()

    def __str__(self) -> str:
        ret = ''
        if self.planet is not None:
            ret += self.planet.name + ' '
        if self.building_item is not None:
            ret += self.building_item.name
            if self.is_shipyard:
                ret += ' (shipyard)'
            if self.is_research:
                ret += ' (research)'
        return ret

    def load_ui(self):
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(1)
        self.setLayout(self._layout)
        # label - planet name (0)
        self._lbl_planetName = QLabel(self)
        self._lbl_planetName.setText('')
        font = self._lbl_planetName.font()
        font.setWeight(QFont.Bold)  # fix label font weight to bold
        self._lbl_planetName.setFont(font)
        self._lbl_planetName.setMinimumWidth(120)
        self._layout.addWidget(self._lbl_planetName)
        # label - planet coords (1)
        self._lbl_planetCoords = QLabel(self)
        self._lbl_planetCoords.setText(' [0:0:0] ')
        self._lbl_planetCoords.setMinimumWidth(70)
        self._layout.addWidget(self._lbl_planetCoords)
        # label - building name (and lvl) (2)
        self._lbl_buildName = QLabel(self)
        self._lbl_buildName.setText('')
        self._lbl_buildName.setMinimumWidth(220)
        self._layout.addWidget(self._lbl_buildName)
        # label - build time left (3)
        self._lbl_buildTime = QLabel(self)
        self._lbl_buildTime.setText('')
        self._lbl_buildTime.setMinimumWidth(70)
        self._layout.addWidget(self._lbl_buildTime)
        # progress bar (4)
        self._pb = QProgressBar(self)
        self._pb.setRange(0, 99)
        self._pb.setValue(0)
        self._layout.addWidget(self._pb)
        # button cancel (5)
        self._btn_cancel = QPushButton(self)
        self._btn_cancel.setText('')
        self._btn_cancel.setIcon(QIcon(':i/cancel.png'))
        self._layout.addWidget(self._btn_cancel)
        self._btn_cancel.clicked.connect(self.on_btn_cancel)

    def hide(self):
        super(Overview_BuildProgressWidget, self).hide()
        self.planet = None
        self.building_item = None
        self.is_shipyard = False
        self.is_research = False

    def _set_percent_complete(self, bi: XNPlanetBuildingItem):
        secs_passed = bi.seconds_total - bi.seconds_left
        percent_complete = (100 * secs_passed) // bi.seconds_total
        self._pb.setValue(percent_complete)

    def _set_buildtime(self, bi: XNPlanetBuildingItem):
        # calc and set time left
        secs_left = bi.seconds_left
        hours_left = secs_left // 3600
        secs_left -= hours_left * 3600
        mins_left = secs_left // 60
        secs_left -= mins_left * 60
        bl_str = '({0:02}:{1:02}:{2:02})'.format(hours_left, mins_left, secs_left)
        self._lbl_buildTime.setText(bl_str)

    def update_from_planet(self, planet: XNPlanet, typ: str = ''):
        self.planet = planet
        self.building_item = None
        self.is_shipyard = False
        self.is_research = False
        # config UI
        self._lbl_planetName.setText(planet.name)
        self._lbl_planetCoords.setText(' [{0}:{1}:{2}] '.format(
            planet.coords.galaxy, planet.coords.system, planet.coords.position))
        if typ == '':
            # set from normal building
            if len(planet.buildings_items) > 0:
                for bi in planet.buildings_items:
                    if bi.is_in_progress():
                        self.building_item = bi
                        self._lbl_buildName.setText('{0} {1} '.format(bi.name, bi.level+1))
                        self._set_percent_complete(bi)
                        self._set_buildtime(bi)
                        return
            return
        elif typ == BPW_TYPE_SHIPYARD:
            self.is_shipyard = True
            self._btn_cancel.setEnabled(False)  # cannot cancel shipyard jobs
            # set from shipyard item
            for bi in planet.shipyard_progress_items:
                self.building_item = bi
                self._lbl_buildName.setText('{0} x {1} '.format(bi.quantity, bi.name))
                self._set_percent_complete(bi)
                self._set_buildtime(bi)
                return
        elif typ == BPW_TYPE_RESEARCH:
            self.is_research = True
            for bi in planet.research_items:
                if bi.is_in_progress():
                    self.building_item = bi
                    self._lbl_buildName.setText('{0} {1} '.format(bi.name, bi.level+1))
                    self._set_percent_complete(bi)
                    self._set_buildtime(bi)
                    self.show()
                    return
            # if we are here, no researches in progress were found (return is in previuos line)
            self.hide()
        else:
            logger.error('update_from_planet(): unknown type: {0}'.format(typ))

    def get_els_widths(self):
        # that is incorrect, we should probably not use widgets widths
        # but instead use layout items geometries
        #plname_w = self._lbl_planetName.width()
        #plcoords_w = self._lbl_planetCoords.width()
        #bname_w = self._lbl_buildName.width()
        #btime_w = self._lbl_buildTime.width()
        # this works the same way :(
        plname_w = self._layout.itemAt(0).geometry().width()
        plcoords_w = self._layout.itemAt(1).geometry().width()
        bname_w = self._layout.itemAt(2).geometry().width()
        btime_w = self._layout.itemAt(3).geometry().width()
        # total width
        ret_w = plname_w + plcoords_w + bname_w + btime_w
        logger.debug('w {0}+{1}+{2}+{3}={4}'.format(plname_w, plcoords_w, bname_w, btime_w, ret_w))
        return  ret_w

    def make_as_wide_as(self, maxwidth: int):
        my_w = self.get_els_widths()
        if my_w >= maxwidth:
            return
        width_not_enough = maxwidth - my_w
        btime_w = self._lbl_buildTime.width()
        self._lbl_buildTime.setMinimumWidth(btime_w + width_not_enough)

    @pyqtSlot()
    def on_btn_cancel(self):
        remove_link = None
        if self.building_item is not None:
            remove_link = self.building_item.remove_link
        logger.debug('Overview_BuildProgressWidget: cancel clicked, remove_link = [{0}]'.\
                     format(remove_link))


# Manages "Overview" tab widget
class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super(OverviewWidget, self).__init__(parent)
        # objects, sub-windows
        self.ui = None
        self._btn_reload = None
        self._aswidget = None
        self.world = XNovaWorld_instance()
        # self.icon_open = None
        # self.icon_closed = None
        # self.prev_index = -1
        self.bp_widgets = dict()  # build progress widgets
        self.bp_widgets_sy = dict()  # shipyard build progress widgets
        self.bp_widgets_res = dict()  # researches build progress widgets

    def load_ui(self):
        # self.icon_open = QIcon(':/i/tb_open.png')
        # self.icon_closed = QIcon(':/i/tb_closed.png')
        # layout
        self._layout = QVBoxLayout()
        self._layout_topbuttons = QHBoxLayout()
        self.setLayout(self._layout)
        self._layout.addLayout(self._layout_topbuttons)
        # sub-windows
        # reload button
        self._btn_reload = QPushButton(self.tr('Refresh overview'), self)
        self._btn_reload.setIcon(QIcon(':i/reload.png'))
        self._btn_reload.clicked.connect(self.on_btn_refresh_overview)
        self._layout_topbuttons.addWidget(self._btn_reload)
        self._layout_topbuttons.addStretch()
        # group box to hold builds info
        self._gb_builds = QGroupBox(self)
        self._gb_builds.setTitle(self.tr('Building Jobs'))
        self._layout_builds = QVBoxLayout()
        self._layout_builds.setContentsMargins(1, 1, 1, 1)
        self._layout_builds.setSpacing(1)
        self._gb_builds.setLayout(self._layout_builds)
        self._layout.addWidget(self._gb_builds)
        # groupbox to hold shipyard builds info
        self._gb_shipyard = QGroupBox(self)
        self._gb_shipyard.setTitle(self.tr('Shipyard Jobs'))
        self._layout_sy = QVBoxLayout()
        self._layout_sy.setContentsMargins(1, 1, 1, 1)
        self._layout_sy.setSpacing(1)
        self._gb_shipyard.setLayout(self._layout_sy)
        self._layout.addWidget(self._gb_shipyard)
        # groupbox to hold researches in progress info
        self._gb_research = QGroupBox(self)
        self._gb_research.setTitle(self.tr('Researches'))
        self._layout_research = QVBoxLayout()
        self._layout_research.setContentsMargins(1, 1, 1, 1)
        self._layout_research.setSpacing(1)
        self._gb_research.setLayout(self._layout_research)
        self._layout.addWidget(self._gb_research)
        # account stats widget
        self._aswidget = Overview_AccStatsWidget(self)
        self._aswidget.load_ui()
        self.layout().addWidget(self._aswidget)
        self._aswidget.show()

    def update_account_info(self):
        a = self.world.get_account_info()
        if self._aswidget is not None:
            self._aswidget.update_account_info(a)

    def get_bpw_for_planet(self, planet_id: int, typ: str='') -> Overview_BuildProgressWidget:
        if typ == '':
            if planet_id in self.bp_widgets:
                return self.bp_widgets[planet_id]
            # create BPW for planet
            bpw = Overview_BuildProgressWidget(self)
            self._layout_builds.addWidget(bpw)
            self.bp_widgets[planet_id] = bpw
            bpw.hide()
            return bpw
        elif typ == BPW_TYPE_SHIPYARD:
            if planet_id in self.bp_widgets_sy:
                return self.bp_widgets_sy[planet_id]
            # create BPW for planet shipyard
            bpw = Overview_BuildProgressWidget(self)
            self._layout_sy.addWidget(bpw)
            self.bp_widgets_sy[planet_id] = bpw
            bpw.hide()
            return bpw
        elif typ == BPW_TYPE_RESEARCH:
            if planet_id in self.bp_widgets_res:
                return self.bp_widgets_res[planet_id]
            # create BPW for planet shipyard
            bpw = Overview_BuildProgressWidget(self)
            self._layout_research.addWidget(bpw)
            self.bp_widgets_res[planet_id] = bpw
            bpw.hide()
            return bpw
        else:
            logger.error('get_bpw_for_planet(): unknown typre requested: {0}'.format(typ))

    def update_builds(self):
        # delete existing build progress widgets (do not do it, just hide)
        for bpw in self.bp_widgets.values():
            bpw.hide()
        for bpw in self.bp_widgets_sy.values():
            bpw.hide()
        planets = self.world.get_planets()
        for pl in planets:
            if pl.has_build_in_progress:
                bpw = self.get_bpw_for_planet(pl.planet_id)
                bpw.show()
                bpw.update_from_planet(pl)
            if len(pl.shipyard_progress_items) > 0:
                bpw = self.get_bpw_for_planet(pl.planet_id, BPW_TYPE_SHIPYARD)
                bpw.show()
                bpw.update_from_planet(pl, BPW_TYPE_SHIPYARD)
            # researches
            bpw = self.get_bpw_for_planet(pl.planet_id, BPW_TYPE_RESEARCH)
            bpw.update_from_planet(pl, BPW_TYPE_RESEARCH)
        # make equal widths (this is not working, why?)
        # self._equalize_builds_widths()

    def _equalize_builds_widths(self):
        maxwidth = -1
        for bpw in self.bp_widgets:
            w = bpw.get_els_widths()
            if w > maxwidth:
                maxwidth = w
        for bpw in self.bp_widgets:
            w = bpw.make_as_wide_as(maxwidth)
        logger.debug('got max width: {0}'.format(maxwidth))

    @pyqtSlot()
    def on_btn_refresh_overview(self):
        self.world.signal(self.world.SIGNAL_RELOAD_PAGE, page_name='overview')
