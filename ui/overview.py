from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QToolBox
from PyQt5.QtGui import QIcon

from .xnova.xn_data import fraction_from_name
from .xnova.xn_world import XNovaWorld_instance
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
        self.ui.gb_account.setTitle(self.tr('Player:'))
        self.ui.tw_accStats.setColumnWidth(0, 120)
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
        # tool box items
        self.ui.toolBox.setItemText(0, self.tr('Overview'))
        self.ui.toolBox.setItemText(1, self.tr('Stats'))
        self.ui.toolBox.setCurrentIndex(1)
        self.ui.toolBox.currentChanged.connect(self.on_tb_currentChanged)

    def set_as_item(self, row: int, col: int, text):
        twi = QTableWidgetItem(str(text))
        self.ui.tw_accStats.setItem(row, col, twi)

    def update_account_info(self):
        a = self.world.get_account_info()
        self.ui.gb_account.setTitle(self.tr('Player: {0} (id={1})').format(a.login, a.id))
        self.set_as_item(0, 1, self.tr('{0} rank {1}').format(
            a.scores.buildings, a.scores.buildings_rank))
        self.set_as_item(1, 1, self.tr('{0} rank {1}').format(
            a.scores.fleet, a.scores.fleet_rank))
        self.set_as_item(2, 1, self.tr('{0} rank {1}').format(
            a.scores.defense, a.scores.defense_rank))
        self.set_as_item(3, 1, self.tr('{0} rank {1}').format(
            a.scores.science, a.scores.science_rank))
        # total: 15156 rank 195 (+2)
        rank_delta_str = '+' + str(a.scores.rank_delta)  # explicit "+" sign
        if a.scores.rank_delta < 0:
            rank_delta_str = str(a.scores.rank_delta)
        self.set_as_item(4, 1, self.tr('{0} rank {1} ({2})').format(
            a.scores.total, a.scores.rank, rank_delta_str))
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

    @pyqtSlot(int)
    def on_tb_currentChanged(self, index):
        logger.debug('current changed: {0}'.format(index))
