from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon

from ui.xnova.xn_data import fraction_from_name, XNAccountInfo, XNPlanetBuildingItem
from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger

from ui.customwidgets.collapsible_frame import CollapsibleFrame
from ui.customwidgets.build_progress_widget import BuildProgressWidget
from ui.widget_utils import number_format


logger = xn_logger.get(__name__, debug=True)


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


# Manages "Overview" tab widget
class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super(OverviewWidget, self).__init__(parent)
        # objects, sub-windows
        self.ui = None
        self._btn_reload = None
        self._aswidget = None
        self.world = XNovaWorld_instance()
        # build progress widgets
        self.bp_widgets = dict()  # build progress widgets
        self.bp_widgets_sy = dict()  # shipyard build progress widgets
        self.bp_widgets_res = dict()  # researches build progress widgets

    def load_ui(self):
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
        self._gb_builds = CollapsibleFrame(self)
        self._gb_builds.setTitle(self.tr('Building Jobs'))
        self._layout.addWidget(self._gb_builds)
        # groupbox to hold shipyard builds info
        self._gb_shipyard = CollapsibleFrame(self)
        self._gb_shipyard.setTitle(self.tr('Shipyard Jobs'))
        self._layout.addWidget(self._gb_shipyard)
        # groupbox to hold researches in progress info
        self._gb_research = CollapsibleFrame(self)
        self._gb_research.setTitle(self.tr('Researches'))
        self._layout.addWidget(self._gb_research)
        # groupbox to hold account stats widget
        self._gb_accstats = CollapsibleFrame(self)
        self._gb_accstats.setTitle(self.tr('Statistics'))
        self._layout.addWidget(self._gb_accstats)
        # account stats widget
        self._aswidget = Overview_AccStatsWidget(self)
        self._aswidget.load_ui()
        self._aswidget.show()
        self._gb_accstats.addWidget(self._aswidget)
        self._gb_accstats.expand()  # staticstics expanded by default
        # add final spacer
        self._layout.addStretch()

    def update_account_info(self):
        a = self.world.get_account_info()
        if self._aswidget is not None:
            self._aswidget.update_account_info(a)

    def get_bpw_for_planet(self, planet_id: int, typ: str='') -> BuildProgressWidget:
        if typ == '':
            if planet_id in self.bp_widgets:
                return self.bp_widgets[planet_id]
            # create BPW for planet
            bpw = BuildProgressWidget(self)
            bpw.requestCancelBuildWithPlanet.connect(self.on_request_build_cancel_with_planet)
            self._gb_builds.addWidget(bpw)
            self.bp_widgets[planet_id] = bpw
            bpw.hide()
            return bpw
        elif typ == BuildProgressWidget.BPW_TYPE_SHIPYARD:
            if planet_id in self.bp_widgets_sy:
                return self.bp_widgets_sy[planet_id]
            # create BPW for planet shipyard
            bpw = BuildProgressWidget(self)
            bpw.requestCancelBuildWithPlanet.connect(self.on_request_build_cancel_with_planet)
            self._gb_shipyard.addWidget(bpw)
            self.bp_widgets_sy[planet_id] = bpw
            bpw.hide()
            return bpw
        elif typ == BuildProgressWidget.BPW_TYPE_RESEARCH:
            if planet_id in self.bp_widgets_res:
                return self.bp_widgets_res[planet_id]
            # create BPW for planet shipyard
            bpw = BuildProgressWidget(self)
            bpw.requestCancelBuildWithPlanet.connect(self.on_request_build_cancel_with_planet)
            self._gb_research.addWidget(bpw)
            self.bp_widgets_res[planet_id] = bpw
            bpw.hide()
            return bpw
        else:
            logger.error('get_bpw_for_planet(): unknown typre requested: {0}'.format(typ))

    def update_builds(self):
        self.setUpdatesEnabled(False)  # big visual changes may follow, stop screen flicker
        # delete existing build progress widgets (do not do it, just hide)
        for bpw in self.bp_widgets.values():
            bpw.hide()
        for bpw in self.bp_widgets_sy.values():
            bpw.hide()
        planets = self.world.get_planets()
        for pl in planets:
            # buildings
            bpw = self.get_bpw_for_planet(pl.planet_id)
            bpw.update_from_planet(pl)
            # shipyard
            if len(pl.shipyard_progress_items) > 0:
                bpw = self.get_bpw_for_planet(pl.planet_id, BuildProgressWidget.BPW_TYPE_SHIPYARD)
                bpw.show()
                bpw.update_from_planet(pl, BuildProgressWidget.BPW_TYPE_SHIPYARD)
            # researches
            bpw = self.get_bpw_for_planet(pl.planet_id, BuildProgressWidget.BPW_TYPE_RESEARCH)
            bpw.update_from_planet(pl, BuildProgressWidget.BPW_TYPE_RESEARCH)
        # make equal widths (this is not working, why?)
        # self._equalize_builds_widths()
        self.setUpdatesEnabled(True)

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

    @pyqtSlot(XNPlanetBuildingItem, int)
    def on_request_build_cancel_with_planet(self, bitem: XNPlanetBuildingItem, planet_id: int):
        self.world.signal(self.world.SIGNAL_BUILD_CANCEL,
                          planet_id=planet_id,
                          bitem=bitem)
