from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon

from .xnova.xn_world import XNovaWorld_instance
from .xnova.xn_data import fraction_from_name
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


# Manages "Overview" tab widget
class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super(OverviewWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/overview.ui'
        # objects, sub-windows
        self.ui = None
        self.world = XNovaWorld_instance()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        self.ui.splitter.setSizes([250, 150])
        self.ui.tw_accStats.setColumnWidth(0, 80)
        self.ui.tw_accStats.setColumnWidth(1, 300)
        # testing only
        self.ui.btn_start.clicked.connect(self.on_btn_start)
        self.ui.btn_stop.clicked.connect(self.on_btn_stop)
        self.ui.btn_signal.clicked.connect(self.on_btn_signal)

    def update_account_info(self):
        def set_as_item(tw, row: int, col: int, text):
            twi = QTableWidgetItem(str(text))
            tw.setItem(row, col, twi)
        a = self.world.get_account_info()
        self.ui.gb_account.setTitle('Player: {0} (id={1})'.format(a.login, a.id))
        set_as_item(self.ui.tw_accStats, 0, 1, '{0} rank {1}'.format(
            a.scores.buildings, a.scores.buildings_rank))
        set_as_item(self.ui.tw_accStats, 1, 1, '{0} rank {1}'.format(
            a.scores.fleet, a.scores.fleet_rank))
        set_as_item(self.ui.tw_accStats, 2, 1, '{0} rank {1}'.format(
            a.scores.defense, a.scores.defense_rank))
        set_as_item(self.ui.tw_accStats, 3, 1, '{0} rank {1}'.format(
            a.scores.science, a.scores.science_rank))
        # total: 15156 rank 195 (+2)
        rank_delta_str = '+' + str(a.scores.rank_delta)  # explicit "+" sign
        if a.scores.rank_delta < 0:
            rank_delta_str = str(a.scores.rank_delta)
        set_as_item(self.ui.tw_accStats, 4, 1, '{0} rank {1} ({2})'.format(
            a.scores.total, a.scores.rank, rank_delta_str))
        set_as_item(self.ui.tw_accStats, 5, 1, '{0} lv ({1}/{2} exp)'.format(
            a.scores.industry_level, a.scores.industry_exp[0], a.scores.industry_exp[1]))
        set_as_item(self.ui.tw_accStats, 6, 1, '{0} lv ({1}/{2} exp)'.format(
            a.scores.military_level, a.scores.military_exp[0], a.scores.military_exp[1]))
        set_as_item(self.ui.tw_accStats, 7, 1, '{0} W / {1} L'.format(a.scores.wins, a.scores.losses))
        set_as_item(self.ui.tw_accStats, 8, 1, a.scores.credits)
        set_as_item(self.ui.tw_accStats, 10, 1, a.alliance_name)
        # fraction
        fr = fraction_from_name(a.scores.fraction)
        if fr:
            icon = QIcon(':/i/{0}'.format(fr.ico_name))
            twi = QTableWidgetItem(icon, str(a.scores.fraction))
            self.ui.tw_accStats.setItem(9, 1, twi)

    # testing only
    @pyqtSlot()
    def on_btn_start(self):
        if not self.world.isRunning():
            logger.debug('starting')
            self.world.start()

    # testing only
    @pyqtSlot()
    def on_btn_stop(self):
        if self.world.isRunning():
            logger.debug('stopping')
            self.world.quit()

    @pyqtSlot()
    def on_btn_signal(self):
        # test exceptions in pyQt slots
        raise Exception("wow")
