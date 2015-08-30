from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox, QToolButton, \
    QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QIcon
from PyQt5 import uic

import datetime

from .xn_world import XNovaWorld_instance
from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class FlightsWidget(QWidget):
    def __init__(self, parent=None):
        super(FlightsWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/flights_widget.ui'
        # objects, sub-windows
        self.ui = None
        self.world = XNovaWorld_instance()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        # configure table widget
        self.ui.tw_flights.setColumnCount(5)
        self.ui.tw_flights.setRowCount(0)
        # timer | mission | src | dst | ships (res)
        self.ui.tw_flights.setHorizontalHeaderLabels(['Timer', 'Mission', 'From', 'To', 'Ships/Res'])
        self.ui.tw_flights.setColumnWidth(0, 120)
        self.ui.tw_flights.setColumnWidth(1, 90)
        self.ui.tw_flights.setColumnWidth(2, 65)
        self.ui.tw_flights.setColumnWidth(3, 65)
        self.ui.tw_flights.setColumnWidth(4, 300)
        self.ui.tw_flights.hide()
        # connections
        self.btn_show.clicked.connect(self.on_showhide_fleets)

    @pyqtSlot()
    def on_showhide_fleets(self):
        if self.ui.tw_flights.isVisible():
            self.ui.tw_flights.hide()
            self.setMinimumHeight(22)
            self.parent().setMinimumHeight(22)
            self.btn_show.setArrowType(Qt.RightArrow)
        else:
            self.ui.tw_flights.show()
            self.setMinimumHeight(22+22+2)
            self.parent().setMinimumHeight(22+22+3)
            self.btn_show.setArrowType(Qt.DownArrow)

    def _set_twi(self, row, col, text):
        twi = QTableWidgetItem(str(text))
        self.ui.tw_flights.setItem(row, col, twi)

    def update_flights(self):
        # clear widget
        self.ui.tw_flights.clearContents()
        self.ui.tw_flights.setRowCount(0)
        # get data
        flights = self.world.get_flights()
        dt_now = datetime.datetime.today()
        irow = 0
        for fl in flights:
            # format data
            # fleet timer
            time_arr_s = str(fl.arrive_datetime)
            td = fl.arrive_datetime - dt_now
            seconds_left = int(td.total_seconds())
            hours_left = seconds_left // 3600
            seconds_left -= (hours_left * 3600)
            minutes_left = seconds_left // 60
            seconds_left -= (minutes_left * 60)
            hours_str = '{0:02}:'.format(hours_left) if hours_left > 0 else ''
            minutes_str = '{0:02}:'.format(minutes_left) if minutes_left > 0 else ''
            seconds_str = '{0:02}'.format(seconds_left)
            timer_str = '{0}{1}{2}\n{3}'.format(hours_str, minutes_str, seconds_str, time_arr_s)
            # fleet mission
            fldir_str = '\n{0}'.format(fl.direction) if fl.direction == 'return' else ''
            mis_str = '{0}{1}'.format(fl.mission, fldir_str)
            # resources
            res_str = '\n{0}'.format(str(fl.res)) if len(fl.res) > 0 else ''
            # insert row
            # timer | mission | src | dst | ships (res)
            self.ui.tw_flights.insertRow(irow)
            self._set_twi(irow, 0, timer_str)
            self._set_twi(irow, 1, mis_str)
            self._set_twi(irow, 2, str(fl.src))
            self._set_twi(irow, 3, str(fl.dst))
            self._set_twi(irow, 4, str(fl.ships) + res_str)
            #
            # self.ui.tw_flights.setRowHeight(irow, 40)
            #
            irow += 1
        self.ui.tw_flights.verticalHeader().resizeSections(QHeaderView.ResizeToContents)
        self.ui.btn_show.setText('Fleets in space: {0}'.format(irow))
