import datetime

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView

from xnova.xn_data import XNFlight
from xnova.xn_world import XNovaWorld_instance
from xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class FlightsWidget(QWidget):
    def __init__(self, parent=None):
        super(FlightsWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/flights_widget.ui'
        # objects, sub-windows
        self.ui = None
        self.world = XNovaWorld_instance()
        self.flights = []
        # our_time - server_time:
        self.diff_with_server_time_secs = 0

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
        self.update_button_fleet_count()

    def update_button_fleet_count(self):
        if self.ui.tw_flights.isVisible():
            self.ui.btn_show.setText('Fleets: {0}'.format(len(self.flights)))
        else:
            closest_fleet_str = ''
            if len(self.flights) > 0:
                fl = self.flights[0]
                secs = self._fl_remaining_time_secs(fl)
                hours = secs // 3600
                secs -= (hours * 3600)
                minutes = secs // 60
                secs -= (minutes * 60)
                return_str = ' ({0})'.format(fl.direction) if fl.direction == 'return' else ''
                closest_fleet_str = '{0:02}:{1:02}:{2:02} {3}{4} {5} => {6}, {7} ship(s)'.format(
                    hours, minutes, secs, fl.mission, return_str,
                    fl.src, fl.dst, len(fl.ships))
            self.ui.btn_show.setText('Fleets: {0}  |||   {1}'.format(
                len(self.flights), closest_fleet_str))

    def _set_twi(self, row, col, text):
        twi = QTableWidgetItem(str(text))
        self.ui.tw_flights.setItem(row, col, twi)

    def _fl_remaining_time_secs(self, fl: XNFlight) -> int:
        our_time = datetime.datetime.today()
        td = fl.arrive_datetime - our_time
        seconds_left = int(td.total_seconds())
        seconds_left += self.diff_with_server_time_secs
        if seconds_left < 0:
            seconds_left = 0
        return seconds_left

    def _fl_timer_str(self, fl: XNFlight) -> str:
        seconds_left = self._fl_remaining_time_secs(fl)
        hours_left = seconds_left // 3600
        seconds_left -= (hours_left * 3600)
        minutes_left = seconds_left // 60
        seconds_left -= (minutes_left * 60)
        hours_str = '{0:02}:'.format(hours_left) if hours_left > 0 else ''
        minutes_str = '{0:02}:'.format(minutes_left) if minutes_left > 0 else ''
        seconds_str = '{0:02}'.format(seconds_left)
        time_arr_s = str(fl.arrive_datetime)
        timer_str = '{0}{1}{2}\n{3}'.format(hours_str, minutes_str, seconds_str, time_arr_s)
        return timer_str

    def update_flights(self):
        # clear widget
        self.ui.tw_flights.clearContents()
        self.ui.tw_flights.setRowCount(0)
        # get data, making a copy of world flights for self
        # because we will modify those (del items when fleet arrives)
        world_flights = self.world.get_flights()
        self.flights = world_flights.copy()
        # calc diff of our time with server time
        our_time = datetime.datetime.today()
        assert isinstance(self.world.server_time, datetime.datetime)
        server_time = self.world.server_time
        dt_diff = our_time - server_time
        # logger.debug(dt_diff.total_seconds())  # 0:00:16.390197
        self.diff_with_server_time_secs = int(dt_diff.total_seconds())
        # iterate
        irow = 0
        for fl in self.flights:
            # format data
            # fleet timer
            timer_str = self._fl_timer_str(fl)
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
        # upadte button text
        self.update_button_fleet_count()

    def flights_tick(self):
        """Updates flights remaining times to display
        """
        our_time = datetime.datetime.today()
        # iterate, updating first column only
        irow = 0
        for fl in self.flights:
            timer_str = self._fl_timer_str(fl)
            self._set_twi(irow, 0, timer_str)
            irow += 1
        # delete completed fleets
        irow = 0
        finished_fleets = []
        for fl in self.flights:
            secs_left = self._fl_remaining_time_secs(fl)
            if secs_left <= 0:
                finished_fleets.append(irow)
            irow += 1
        for irow in finished_fleets:
            self.ui.tw_flights.removeRow(irow)
            del self.flights[irow]
        # also update button text
        self.update_button_fleet_count()
