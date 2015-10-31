import pathlib
import pickle

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QMessageBox, QSystemTrayIcon, \
    QLayout, QBoxLayout, QLayoutItem
from PyQt5.QtGui import QIcon, QCloseEvent

from .widget_utils import install_layout_for_widget, append_trailing_spacer_to_layout, \
    remove_trailing_spacer_from_layout, flight_mission_for_humans
from .statusbar import XNCStatusBar
from .login_widget import LoginWidget
from .flights_widget import FlightsWidget
from .planets_panel import PlanetsBarWidget
from .overview import OverviewWidget
from .imperium import ImperiumWidget

from .xnova.xn_data import XNCoords, XNFlight, XNPlanet
from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


# This class will control:
# 1. main application window in general, and all UI (tray icon, etc)
#    (although each tab will have its own widget controller)
# 2. XNova world object and background world updater thread
class XNova_MainWindow(QWidget):

    STATE_NOT_AUTHED = 0
    STATE_AUTHED = 1

    def __init__(self, parent=None):
        super(XNova_MainWindow, self).__init__(parent)
        # state vars
        self.uifile = 'ui/main.ui'
        self.config_store_dir = './cache'
        self.state = self.STATE_NOT_AUTHED
        self.login_email = ''
        self.cookies_dict = {}
        # objects, sub-windows
        self.ui = None
        self.tray_icon = None
        self.statusbar = None
        self.login_widget = None
        self.flights_widget = None
        self.overview_widget = None
        self.imperium_widget = None
        # initialization
        self.load_ui()
        self.world = XNovaWorld_instance()
        self.world_timer = QTimer(self)
        self.world_timer.timeout.connect(self.on_world_timer)

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        self.setWindowIcon(QIcon(':/i/favicon_32.png'))
        if QSystemTrayIcon.isSystemTrayAvailable():
            logger.debug('System tray icon is available, showing')
            self.tray_icon = QSystemTrayIcon(QIcon(':/i/favicon_16.png'), self)
            self.tray_icon.setToolTip(self.tr('XNova Commander'))
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            self.tray_icon.show()
        # create status bar
        self.statusbar = XNCStatusBar(self)
        self.layout().addWidget(self.statusbar)
        self.setStatusMessage(self.tr('Not connected: Log in!'))
        # try to restore last window size
        ssz = self.load_cfg_val('main_size')
        if ssz is not None:
            self.resize(ssz[0], ssz[1])

    # overrides QWidget.closeEvent
    # cleanup just before the window close
    def closeEvent(self, close_event: QCloseEvent):
        logger.debug('closing')
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        if self.world_timer.isActive():
            self.world_timer.stop()
        if self.world.isRunning():
            self.world.quit()
            logger.debug('waiting for world thread to stop (5 sec)...')
            wait_res = self.world.wait(5000)
            if not wait_res:
                logger.warn('wait failed, last chance, terminating!')
                self.world.terminate()
        # store window size
        ssz = (self.width(), self.height())
        self.store_cfg_val('main_size', ssz)
        # accept the event
        close_event.accept()

    def setStatusMessage(self, msg: str):
        self.statusbar.setStatus(msg)

    def store_cfg_val(self, category: str, value):
        pickle_filename = '{0}/{1}.dat'.format(self.config_store_dir, category)
        try:
            cache_dir = pathlib.Path(self.config_store_dir)
            if not cache_dir.exists():
                cache_dir.mkdir()
            with open(pickle_filename, 'wb') as f:
                pickle.dump(value, f)
        except pickle.PickleError as pe:
            pass
        except IOError as ioe:
            pass

    def load_cfg_val(self, category: str, default_value=None):
        value = None
        pickle_filename = '{0}/{1}.dat'.format(self.config_store_dir, category)
        try:
            with open(pickle_filename, 'rb') as f:
                value = pickle.load(f)
                if value is None:
                    value = default_value
        except pickle.PickleError as pe:
            pass
        except IOError as ioe:
            pass
        return value

    # called by main application object just after main window creation
    # to show login widget and begin login process
    def begin_login(self):
        # create and show login widget as first tab
        self.login_widget = LoginWidget(self.ui.tabWidget)
        self.login_widget.load_ui()
        self.login_widget.loginError.connect(self.on_login_error)
        self.login_widget.loginOk.connect(self.on_login_ok)
        tab_index = self.ui.tabWidget.addTab(self.login_widget, self.tr('Login'))
        self.login_widget.show()
        #self.add_tab(self.login_widget, self.tr('Login'))
        #
        # testing only - add 'fictive' planets to test planets panel without loading
        # pl1 = XNPlanet('Arnon', XNCoords(1, 7, 6))
        # pl1.pic_url = 'skins/default/planeten/small/s_normaltempplanet08.jpg'
        # pl1.fields_busy = 90
        # pl1.fields_total = 167
        # pl1.is_current = True
        # pl2 = XNPlanet('Safizon', XNCoords(1, 232, 7))
        # pl2.pic_url = 'skins/default/planeten/small/s_dschjungelplanet05.jpg'
        # pl2.fields_busy = 84
        # pl2.fields_total = 207
        # pl2.is_current = False
        # test_planets = [pl1, pl2]
        # self.setup_planets_panel(test_planets)

    def setup_planets_panel(self, planets: list):
        layout = self.ui.panel_planets.layout()
        layout.setSpacing(0)
        remove_trailing_spacer_from_layout(layout)
        # remove all previous planet widgets from planets panel
        if layout.count() > 0:
            for i in range(layout.count()-1, -1, -1):
                li = layout.itemAt(i)
                if li is not None:
                    wi = li.widget()
                    if wi is not None:
                        if isinstance(wi, PlanetsBarWidget):
                            layout.removeWidget(wi)
                            wi.close()
                            del wi
        for pl in planets:
            pw = PlanetsBarWidget(self.ui.panel_planets)
            pw.setPlanet(pl)
            layout.addWidget(pw)
            pw.show()
        append_trailing_spacer_to_layout(layout)

    def update_planets_panel(self):
        """
        Calls QWidget.update() on every PlanetBarWidget
        embedded in ui.panel_planets, causing repaint
        """
        layout = self.ui.panel_planets.layout()
        if layout.count() > 0:
            for i in range(layout.count()):
                li = layout.itemAt(i)
                if li is not None:
                    wi = li.widget()
                    if wi is not None:
                        if isinstance(wi, PlanetsBarWidget):
                            wi.update()

    @pyqtSlot(str)
    def on_login_error(self, errstr):
        logger.error('Login error: {0}'.format(errstr))
        self.state = self.STATE_NOT_AUTHED
        self.setStatusMessage(self.tr('Login error: {0}').format(errstr))
        QMessageBox.critical(self, self.tr('Login error:'), errstr)

    @pyqtSlot(str, dict)
    def on_login_ok(self, login_email, cookies_dict):
        # logger.debug('Login OK, login: {0}, cookies: {1}'.format(login_email, str(cookies_dict)))
        # save login data: email, cookies
        self.state = self.STATE_AUTHED
        self.setStatusMessage(self.tr('Login OK, loading world'))
        self.login_email = login_email
        self.cookies_dict = cookies_dict
        #
        # destroy login widget and remove its tab
        self.ui.tabWidget.removeTab(0)
        self.login_widget.close()
        self.login_widget = None
        #
        # create all main widgets
        # create flights widget
        self.flights_widget = FlightsWidget(self.ui.fr_flights)
        self.flights_widget.load_ui()
        install_layout_for_widget(self.ui.fr_flights, Qt.Vertical, margins=(1, 1, 1, 1), spacing=1)
        self.ui.fr_flights.layout().addWidget(self.flights_widget)
        self.flights_widget.setEnabled(False)
        #
        # create overview widget and add it as first tab
        self.overview_widget = OverviewWidget(self)
        self.overview_widget.load_ui()
        tab_index = self.ui.tabWidget.addTab(self.overview_widget, self.tr('Overview'))
        self.overview_widget.show()
        self.overview_widget.setEnabled(False)
        #
        # create 2nd tab - Imperium
        self.imperium_widget = ImperiumWidget(self.ui.tabWidget)
        tab_index = self.ui.tabWidget.addTab(self.imperium_widget, self.tr('Imperium'))
        self.imperium_widget.setEnabled(False)
        # initialize XNova world updater
        self.world.initialize(cookies_dict)
        self.world.set_login_email(self.login_email)
        self.world.world_load_progress.connect(self.on_world_load_progress)
        self.world.world_load_complete.connect(self.on_world_load_complete)
        self.world.flight_arrived.connect(self.on_flight_arrived)
        self.world.loaded_overview.connect(self.on_loaded_overview)
        self.world.start()

    @pyqtSlot(str, int)
    def on_world_load_progress(self, comment: str, progress: int):
        msg = self.tr('Loading world') + ' ({0}%) {1}...'.format(progress, comment)
        self.setStatusMessage(msg)

    @pyqtSlot()
    def on_world_load_complete(self):
        logger.debug('main: on_world_load_complete()')
        self.setStatusMessage(self.tr('World loaded.'))
        # update account info
        if self.overview_widget is not None:
            self.overview_widget.setEnabled(True)
            self.overview_widget.update_account_info()
        # update flying fleets
        self.flights_widget.setEnabled(True)
        self.flights_widget.update_flights()
        # update planets
        planets = self.world.get_planets()
        self.setup_planets_panel(planets)
        if self.imperium_widget is not None:
            self.imperium_widget.setEnabled(True)
            self.imperium_widget.update_planets()
        # set timer to do every-second world recalculation
        self.world_timer.setInterval(1000)
        self.world_timer.setSingleShot(False)
        self.world_timer.start()

    @pyqtSlot()
    def on_loaded_overview(self):
        logger.debug('on_loaded_overview')
        # A lot of things are updated when overview is loaded
        #  * Account information and stats
        if self.overview_widget is not None:
            self.overview_widget.update_account_info()
        #  * flights will be updated every second anyway in on_world_timer(), so no need to call
        #    self.flights_widget.update_flights()
        #  * messages count also, is updated with flights
        #  * current planet may have changed
        self.update_planets_panel()
        #  * server time is updated also

    @pyqtSlot()
    def on_world_timer(self):
        if self.world:
            self.world.world_tick()
        if self.flights_widget:
            self.flights_widget.update_flights()

    @pyqtSlot(int)
    def on_tray_icon_activated(self, reason):
        # QSystemTrayIcon::Unknown	0	Unknown reason
        # QSystemTrayIcon::Context	1	The context menu for the system tray entry was requested
        # QSystemTrayIcon::DoubleClick	2	The system tray entry was double clicked
        # QSystemTrayIcon::Trigger	3	The system tray entry was clicked
        # QSystemTrayIcon::MiddleClick	4	The system tray entry was clicked with the middle mouse button
        if reason == QSystemTrayIcon.Trigger:
            # left-click
            self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            self.show()
            return

    def show_tray_message(self, title, message, icon_type=None, timeout_ms=None):
        """
        Shows message from system tray icon, if system supports it.
        If no support, this is just a no-op
        :param title: message title
        :param message: message text
        :param icon_type: one of:
        QSystemTrayIcon.NoIcon      0   No icon is shown.
        QSystemTrayIcon.Information 1   An information icon is shown.
        QSystemTrayIcon.Warning     2   A standard warning icon is shown.
        QSystemTrayIcon.Critical    3   A critical warning icon is shown
        """
        if self.tray_icon is None:
            return
        if self.tray_icon.supportsMessages():
            if icon_type is None:
                icon_type = QSystemTrayIcon.Information
            if timeout_ms is None:
                timeout_ms = 10000
            self.tray_icon.showMessage(title, message, icon_type, timeout_ms)
        else:
            logger.info('This system does not support tray icon messages.')

    @pyqtSlot(XNFlight)
    def on_flight_arrived(self, fl: XNFlight):
        logger.debug('main window got flight arrival: {0}'.format(fl))
        mis_str = flight_mission_for_humans(fl.mission)
        if fl.direction == 'return':
            mis_str += ' ' + self.tr('return')
        short_fleet_info = self.tr('{0} {1} => {2}, {3} ship(s)').format(
            mis_str, fl.src, fl.dst, len(fl.ships))
        self.show_tray_message(self.tr('XNova: Fleet arrived'), short_fleet_info)
