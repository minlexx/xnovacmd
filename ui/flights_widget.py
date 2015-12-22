from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QPushButton
from PyQt5.QtGui import QColor, QBrush, QIcon

from .widget_utils import flight_mission_for_humans, number_format
from ui.customwidgets.my_buttons import ButtonTextOverIcon

from .xnova.xn_data import XNFlight
from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class FlightsWidget(QWidget):

    requestShowSettings = pyqtSignal()
    requestShowMessages = pyqtSignal()

    def __init__(self, parent=None):
        super(FlightsWidget, self).__init__(parent)
        # state vars
        self.uifile = 'ui/flights_widget.ui'
        # objects, sub-windows
        self.ui = None
        self._btn_newmsg = ButtonTextOverIcon(self)
        self._btn_settings = QPushButton(self)
        # world reference
        self.world = XNovaWorld_instance()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        # new messages button
        self._btn_newmsg.setText('')
        self._btn_newmsg.setIcon(QIcon(':/i/message.png'))
        self._btn_newmsg.setIconSize(QSize(24, 16))
        self._btn_newmsg.setMinimumSize(QSize(30, 22))
        self._btn_newmsg.setMaximumSize(QSize(30, 22))
        self.ui.horizontalLayout.insertWidget(0, self._btn_newmsg, 0)
        # settings button
        self._btn_settings.setText('')
        self._btn_settings.setIcon(QIcon(':/i/settings_32.png'))
        self._btn_settings.setIconSize(QSize(16, 16))
        self._btn_settings.setMaximumWidth(32)
        self._btn_settings.clicked.connect(self.on_btn_settings)
        self.ui.horizontalLayout.addWidget(self._btn_settings, 0)
        # configure table widget
        self.ui.tw_flights.setColumnCount(5)
        self.ui.tw_flights.setRowCount(0)
        # timer | mission | src | dst | ships (res)
        self.ui.tw_flights.setHorizontalHeaderLabels([
            self.tr('Timer'), self.tr('Mission'), self.tr('From'),
            self.tr('To'), self.tr('Ships/Res')])
        self.ui.tw_flights.setColumnWidth(0, 120)
        self.ui.tw_flights.setColumnWidth(1, 90)
        self.ui.tw_flights.setColumnWidth(2, 120)
        self.ui.tw_flights.setColumnWidth(3, 120)
        self.ui.tw_flights.setColumnWidth(4, 350)  # wider, wider
        self.ui.tw_flights.hide()
        # connections
        self.btn_show.clicked.connect(self.on_showhide_fleets)
        self._btn_newmsg.clicked.connect(self.on_messages_clicked)

    def set_online_state(self, st: bool = True):
        self._btn_newmsg.setEnabled(st)
        self.ui.btn_show.setEnabled(st)

    #def minimize_height(self):
    #    print(self.parent())
    #    num_rows = self.ui.tw_flights.rowCount()
    #    total_heights = 0
    #    for i in range(num_rows):
    #        total_heights += self.ui.tw_flights.rowHeight(i)
    #    if total_heights < 10:
    #        total_heights = 10
    #    # add vertical header height
    #    header_view = self.ui.tw_flights.verticalHeader()
    #    if header_view is not None:
    #        total_heights += header_view.height()
    #    self.ui.tw_flights.setMaximumHeight(total_heights)

    @pyqtSlot()
    def on_showhide_fleets(self):
        if self.ui.tw_flights.isVisible():
            self.ui.tw_flights.hide()
            self.setMinimumHeight(22)
            self.parent().setMinimumHeight(22)
            self.btn_show.setArrowType(Qt.RightArrow)
        else:
            self.ui.tw_flights.show()
            base_h = 22 + 22
            grow_h = 100
            self.setMinimumHeight(base_h + grow_h)
            self.parent().setMinimumHeight(base_h + grow_h + 1)
            self.btn_show.setArrowType(Qt.DownArrow)
            # self.minimize_height()
        self.update_button_fleet_count()

    def update_button_fleet_count(self):
        flights = self.world.get_flights()
        flights_cnt = self.world.get_fleets_count()
        #
        fleets_count_str = '{0} / {1}'.format(flights_cnt[0], flights_cnt[1])
        #
        if self.ui.tw_flights.isVisible():
            self.ui.btn_show.setText(self.tr('Fleets: {0}').format(fleets_count_str))
        else:
            closest_fleet_str = ''
            if len(flights) > 0:
                fl = flights[0]
                secs = self.world.get_flight_remaining_time_secs(fl)
                if secs == -1:  # ignore, this should not happen but possible
                    secs = 0
                hours = secs // 3600
                secs -= (hours * 3600)
                minutes = secs // 60
                secs -= (minutes * 60)
                return_str = self.tr(' (return)') if fl.direction == 'return' else ''
                closest_fleet_str = self.tr('{0:02}:{1:02}:{2:02} ||| {3}{4}: {5} => {6}, {7} ship(s)').format(
                    hours, minutes, secs,
                    flight_mission_for_humans(fl.mission),
                    return_str,
                    fl.src, fl.dst, len(fl.ships))
            self.ui.btn_show.setText(self.tr('Fleets: {0}  |||  {1}').format(
                fleets_count_str, closest_fleet_str))

    def update_new_messages_count(self):
        nmc = self.world.get_new_messages_count()
        txt = ''
        if nmc > 0:
            txt = str(nmc)
        self._btn_newmsg.setText(txt)
        self._btn_newmsg.update()

    @staticmethod
    def _get_mis_bgcolor(mis: str, dir_: str) -> QColor:
        ret = QColor(255, 255, 255)
        if mis == 'ownharvest':
            ret = QColor(255, 255, 200)
        elif mis == 'owndeploy':
            ret = QColor(200, 200, 255)
        elif mis == 'ownattack':
            ret = QColor(255, 200, 230)
        elif mis == 'owntransport':
            ret = QColor(200, 255, 200)
        elif mis == 'ownespionage':
            ret = QColor(255, 220, 150)
        elif mis == 'owncolony':
            ret = QColor(190, 210, 255)
        elif mis == 'ownmissile':
            ret = QColor(165, 255, 255)
        elif mis == 'ownbase':
            ret = QColor(153, 200, 255)
        elif mis == 'attack':
            ret = QColor(255, 230, 230)
        if dir_ == 'return':
            # darken
            ret.setRed(ret.red() * 0.8)
            ret.setGreen(ret.green() * 0.8)
            ret.setBlue(ret.blue() * 0.8)
        return ret

    @staticmethod
    def _get_mis_fgcolor(mis: str) -> QColor:
        ret = QColor(0, 0, 0)
        if mis == 'attack':
            ret = QColor(200, 0, 0)
        return ret

    def _set_twi(self, row, col, text, bg_color=None, fg_color=None):
        twi = QTableWidgetItem(str(text))
        if bg_color is not None:
            bgb = QBrush(QColor(bg_color), Qt.SolidPattern)
            twi.setBackground(bgb)
        if fg_color is not None:
            fgb = QBrush(QColor(fg_color), Qt.SolidPattern)
            twi.setForeground(fgb)
        self.ui.tw_flights.setItem(row, col, twi)

    def _fl_timer_str(self, fl: XNFlight) -> str:
        seconds_left = self.world.get_flight_remaining_time_secs(fl)
        if seconds_left == -1:
            raise ValueError('Flight seconds left == -1: {0}'.format(str(fl)))
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
        # prev_row = self.ui.tw_flights.currentRow()
        # prev_col = self.ui.tw_flights.currentColumn()
        self.ui.tw_flights.setUpdatesEnabled(False)
        self.ui.tw_flights.clearContents()
        # self.ui.tw_flights.setRowCount(0)  # nope, resets current scroll position
        # get data
        flights = self.world.get_flights()
        self.ui.tw_flights.setRowCount(len(flights))
        # iterate
        irow = 0
        for fl in flights:
            # format data
            # fleet timer
            timer_str = self._fl_timer_str(fl)
            # fleet mission
            fldir_str = self.tr('\nreturn') if fl.direction == 'return' else ''
            mis_str_h = flight_mission_for_humans(fl.mission)
            mis_str = '{0}{1}'.format(mis_str_h, fldir_str)
            # resources
            res_str = ''
            if len(fl.res) > 0:
                res_str = '\n' + self.tr('Res: {0} m / {1} c {2} d').format(
                    number_format(fl.res.met),
                    number_format(fl.res.cry),
                    number_format(fl.res.deit))
            # insert row
            # timer | mission | src | dst | ships (res)
            # self.ui.tw_flights.insertRow(irow)
            self._set_twi(irow, 0, timer_str)
            self._set_twi(irow, 1, mis_str,
                          self._get_mis_bgcolor(fl.mission, fl.direction),
                          self._get_mis_fgcolor(fl.mission))
            self._set_twi(irow, 2, str(fl.src))
            self._set_twi(irow, 3, str(fl.dst))
            self._set_twi(irow, 4, str(fl.ships) + res_str)
            # self.ui.tw_flights.setRowHeight(irow, 40)
            irow += 1
        self.ui.tw_flights.setUpdatesEnabled(True)
        # self.ui.tw_flights.setCurrentCell(prev_row, prev_col)
        self.ui.tw_flights.horizontalHeader().setStretchLastSection(True)
        self.ui.tw_flights.verticalHeader().resizeSections(QHeaderView.ResizeToContents)
        # upadte button text
        self.update_button_fleet_count()
        self.update_new_messages_count()

    @pyqtSlot()
    def on_messages_clicked(self):
        self.requestShowMessages.emit()

    @pyqtSlot()
    def on_btn_settings(self):
        self.requestShowSettings.emit()
