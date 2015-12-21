import pathlib
import pickle
import configparser

from PyQt5.QtCore import pyqtSlot, Qt, QTimer, QVariant, QEvent
from PyQt5.QtWidgets import QWidget, QFrame, QMessageBox, QSystemTrayIcon, \
    QScrollArea, QMenu, QAction, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon, QCloseEvent, QCursor, QShowEvent, QWindowStateChangeEvent

from .statusbar import XNCStatusBar
from .settings_widget import SettingsWidget
from .login_widget import LoginWidget
from .flights_widget import FlightsWidget
from .overview import OverviewWidget
from .imperium_widget import ImperiumWidget
from .galaxy_widget import GalaxyWidget
from .planet_widget import PlanetWidget

from .customwidgets.planets_bar_widget import PlanetsBarWidget
from .customwidgets.xtabwidget import XTabWidget

from .widget_utils import install_layout_for_widget, \
    append_trailing_spacer_to_layout, \
    remove_trailing_spacer_from_layout, \
    flight_mission_for_humans

from .xnova.xn_data import XNCoords, XNFlight, XNPlanet, XNPlanetBuildingItem
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
        super(XNova_MainWindow, self).__init__(parent, Qt.Window)
        # state vars
        self.config_store_dir = './cache'
        self.cfg = configparser.ConfigParser()
        self.cfg.read('config/net.ini', encoding='utf-8')
        self.state = self.STATE_NOT_AUTHED
        self.login_email = ''
        self.cookies_dict = {}
        self._hidden_to_tray = False
        #
        # init UI
        self.setWindowIcon(QIcon(':/i/xnova_logo_64.png'))
        self.setWindowTitle('XNova Commander')
        # main layouts
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 2, 0, 0)
        self._layout.setSpacing(3)
        self.setLayout(self._layout)
        self._horizontal_layout = QHBoxLayout()
        self._horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self._horizontal_layout.setSpacing(6)
        # flights frame
        self._fr_flights = QFrame(self)
        self._fr_flights.setMinimumHeight(22)
        self._fr_flights.setFrameShape(QFrame.NoFrame)
        self._fr_flights.setFrameShadow(QFrame.Plain)
        # planets bar scrollarea
        self._sa_planets = QScrollArea(self)
        self._sa_planets.setMinimumWidth(125)
        self._sa_planets.setMaximumWidth(125)
        self._sa_planets.setFrameShape(QFrame.NoFrame)
        self._sa_planets.setFrameShadow(QFrame.Plain)
        self._sa_planets.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._sa_planets.setWidgetResizable(True)
        self._panel_planets = QWidget(self._sa_planets)
        self._layout_pp = QVBoxLayout()
        self._panel_planets.setLayout(self._layout_pp)
        self._lbl_planets = QLabel(self.tr('Planets:'), self._panel_planets)
        self._lbl_planets.setMaximumHeight(32)
        self._layout_pp.addWidget(self._lbl_planets)
        self._layout_pp.addStretch()
        self._sa_planets.setWidget(self._panel_planets)
        #
        # tab widget
        self._tabwidget = XTabWidget(self)
        self._tabwidget.enableButtonAdd(False)
        self._tabwidget.tabCloseRequested.connect(self.on_tab_close_requested)
        self._tabwidget.addClicked.connect(self.on_tab_add_clicked)
        #
        # create status bar
        self._statusbar = XNCStatusBar(self)
        self.setStatusMessage(self.tr('Not connected: Log in!'))
        #
        # tab widget pages
        self.login_widget = None
        self.flights_widget = None
        self.overview_widget = None
        self.imperium_widget = None
        #
        # settings widget
        self.settings_widget = SettingsWidget(self)
        self.settings_widget.settings_changed.connect(self.on_settings_changed)
        self.settings_widget.hide()
        #
        # finalize layouts
        self._horizontal_layout.addWidget(self._sa_planets)
        self._horizontal_layout.addWidget(self._tabwidget)
        self._layout.addWidget(self._fr_flights)
        self._layout.addLayout(self._horizontal_layout)
        self._layout.addWidget(self._statusbar)
        #
        # system tray icon
        self.tray_icon = None
        show_tray_icon = False
        if 'tray' in self.cfg:
            if (self.cfg['tray']['icon_usage'] == 'show') or \
                    (self.cfg['tray']['icon_usage'] == 'show_min'):
                self.create_tray_icon()
        #
        # try to restore last window size
        ssz = self.load_cfg_val('main_size')
        if ssz is not None:
            self.resize(ssz[0], ssz[1])
        #
        # world initialization
        self.world = XNovaWorld_instance()
        self.world_timer = QTimer(self)
        self.world_timer.timeout.connect(self.on_world_timer)

    # overrides QWidget.closeEvent
    # cleanup just before the window close
    def closeEvent(self, close_event: QCloseEvent):
        logger.debug('closing')
        if self.tray_icon is not None:
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

    def showEvent(self, evt: QShowEvent):
        super(XNova_MainWindow, self).showEvent(evt)
        self._hidden_to_tray = False

    def changeEvent(self, evt: QEvent):
        super(XNova_MainWindow, self).changeEvent(evt)
        if evt.type() == QEvent.WindowStateChange:
            if not isinstance(evt, QWindowStateChangeEvent):
                return
            # make sure we only do this for minimize events
            if (evt.oldState() != Qt.WindowMinimized) and self.isMinimized():
                # we were minimized! explicitly hide settings widget
                #     if it is open, otherwise it will be lost forever :(
                if self.settings_widget is not None:
                    if self.settings_widget.isVisible():
                        self.settings_widget.hide()
                # should we minimize to tray?
                if self.cfg['tray']['icon_usage'] == 'show_min':
                    if not self._hidden_to_tray:
                        self._hidden_to_tray = True
                        self.hide()

    def create_tray_icon(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            logger.debug('System tray icon is available, showing')
            self.tray_icon = QSystemTrayIcon(QIcon(':/i/xnova_logo_32.png'), self)
            self.tray_icon.setToolTip(self.tr('XNova Commander'))
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            self.tray_icon.show()
        else:
            self.tray_icon = None

    def hide_tray_icon(self):
        if self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None

    def set_tray_tooltip(self, tip: str):
        if self.tray_icon is not None:
            self.tray_icon.setToolTip(tip)

    def setStatusMessage(self, msg: str):
        self._statusbar.set_status(msg)

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

    @pyqtSlot()
    def on_settings_changed(self):
        self.cfg.read('config/net.ini', encoding='utf-8')
        # maybe show/hide tray icon now?
        show_tray_icon = False
        if 'tray' in self.cfg:
            icon_usage = self.cfg['tray']['icon_usage']
            if (icon_usage == 'show') or (icon_usage == 'show_min'):
                show_tray_icon = True
        # show if needs show and hidden, or hide if shown and needs to hide
        if show_tray_icon and (self.tray_icon is None):
            logger.debug('settings changed, showing tray icon')
            self.create_tray_icon()
        elif (not show_tray_icon) and (self.tray_icon is not None):
            logger.debug('settings changed, hiding tray icon')
            self.hide_tray_icon()
        # also notify world about changed config!
        self.world.reload_config()

    def add_tab(self, widget: QWidget, title: str, closeable: bool = True) -> int:
        tab_index = self._tabwidget.addTab(widget, title, closeable)
        return tab_index

    def remove_tab(self, index: int):
        self._tabwidget.removeTab(index)

    # called by main application object just after main window creation
    # to show login widget and begin login process
    def begin_login(self):
        # create flights widget
        self.flights_widget = FlightsWidget(self._fr_flights)
        self.flights_widget.load_ui()
        install_layout_for_widget(self._fr_flights, Qt.Vertical, margins=(1, 1, 1, 1), spacing=1)
        self._fr_flights.layout().addWidget(self.flights_widget)
        self.flights_widget.set_online_state(False)
        self.flights_widget.requestShowSettings.connect(self.on_show_settings)
        # create and show login widget as first tab
        self.login_widget = LoginWidget(self._tabwidget)
        self.login_widget.load_ui()
        self.login_widget.loginError.connect(self.on_login_error)
        self.login_widget.loginOk.connect(self.on_login_ok)
        self.login_widget.show()
        self.add_tab(self.login_widget, self.tr('Login'), closeable=False)
        # self.test_setup_planets_panel()
        self.test_planet_tab()

    def setup_planets_panel(self, planets: list):
        layout = self._panel_planets.layout()
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
            pw = PlanetsBarWidget(self._panel_planets)
            pw.setPlanet(pl)
            layout.addWidget(pw)
            pw.show()
            # connections from each planet bar widget
            pw.requestOpenGalaxy.connect(self.on_request_open_galaxy_tab)
            pw.requestOpenPlanet.connect(self.on_request_open_planet_tab)
        append_trailing_spacer_to_layout(layout)

    def update_planets_panel(self):
        """
        Calls QWidget.update() on every PlanetBarWidget
        embedded in ui.panel_planets, causing repaint
        """
        layout = self._panel_planets.layout()
        if layout.count() > 0:
            for i in range(layout.count()):
                li = layout.itemAt(i)
                if li is not None:
                    wi = li.widget()
                    if wi is not None:
                        if isinstance(wi, PlanetsBarWidget):
                            wi.update()

    def add_tab_for_planet(self, planet: XNPlanet):
        # construct planet widget and setup signals/slots
        plw = PlanetWidget(self._tabwidget)
        plw.requestOpenGalaxy.connect(self.on_request_open_galaxy_tab)
        plw.setPlanet(planet)
        # construct tab title
        tab_title = '{0} {1}'.format(planet.name, planet.coords.coords_str())
        # add tab and make it current
        tab_index = self.add_tab(plw, tab_title, closeable=True)
        self._tabwidget.setCurrentIndex(tab_index)
        self._tabwidget.tabBar().setTabIcon(tab_index, QIcon(':/i/planet_32.png'))
        return tab_index

    def add_tab_for_galaxy(self, coords: XNCoords = None):
        gw = GalaxyWidget(self._tabwidget)
        tab_title = '{0}'.format(self.tr('Galaxy'))
        if coords is not None:
            tab_title = '{0} {1}'.format(self.tr('Galaxy'), coords.coords_str())
            gw.setCoords(coords.galaxy, coords.system)
        idx = self.add_tab(gw, tab_title, closeable=True)
        self._tabwidget.setCurrentIndex(idx)
        self._tabwidget.tabBar().setTabIcon(idx, QIcon(':/i/galaxy_32.png'))

    @pyqtSlot(int)
    def on_tab_close_requested(self, idx: int):
        # logger.debug('tab close requested: {0}'.format(idx))
        if idx <= 1:  # cannot close overview or imperium tabs
            return
        self.remove_tab(idx)

    @pyqtSlot()
    def on_tab_add_clicked(self):
        pos = QCursor.pos()
        planets = self.world.get_planets()
        # logger.debug('tab bar add clicked, cursor pos = ({0}, {1})'.format(pos.x(), pos.y()))
        menu = QMenu(self)
        # galaxy view
        galaxy_action = QAction(menu)
        galaxy_action.setText(self.tr('Add galaxy view'))
        galaxy_action.setData(QVariant('galaxy'))
        menu.addAction(galaxy_action)
        # planets
        menu.addSection(self.tr('-- Planet tabs: --'))
        for planet in planets:
            action = QAction(menu)
            action.setText('{0} {1}'.format(planet.name, planet.coords.coords_str()))
            action.setData(QVariant(planet.planet_id))
            menu.addAction(action)
        action_ret = menu.exec(pos)
        if action_ret is not None:
            logger.debug('selected action data = {0}'.format(str(action_ret.data())))
            if action_ret == galaxy_action:
                logger.debug('action_ret == galaxy_action')
                self.add_tab_for_galaxy()
                return
            # else consider this is planet widget
            planet_id = int(action_ret.data())
            planet = self.world.get_planet(planet_id)
            if planet is not None:
                self.add_tab_for_planet(planet)

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
        self.remove_tab(0)
        self.login_widget.close()
        self.login_widget = None
        #
        # create overview widget and add it as first tab
        self.overview_widget = OverviewWidget(self._tabwidget)
        self.overview_widget.load_ui()
        self.add_tab(self.overview_widget, self.tr('Overview'), closeable=False)
        self.overview_widget.show()
        self.overview_widget.setEnabled(False)
        #
        # create 2nd tab - Imperium
        self.imperium_widget = ImperiumWidget(self._tabwidget)
        self.add_tab(self.imperium_widget, self.tr('Imperium'), closeable=False)
        self.imperium_widget.setEnabled(False)
        #
        # initialize XNova world updater
        self.world.initialize(cookies_dict)
        self.world.set_login_email(self.login_email)
        # connect signals from world
        self.world.world_load_progress.connect(self.on_world_load_progress)
        self.world.world_load_complete.connect(self.on_world_load_complete)
        self.world.flight_arrived.connect(self.on_flight_arrived)
        self.world.build_complete.connect(self.on_building_complete)
        self.world.loaded_overview.connect(self.on_loaded_overview)
        self.world.loaded_imperium.connect(self.on_loaded_imperium)
        self.world.start()

    @pyqtSlot(str, int)
    def on_world_load_progress(self, comment: str, progress: int):
        self._statusbar.set_world_load_progress(comment, progress)

    @pyqtSlot()
    def on_world_load_complete(self):
        logger.debug('main: on_world_load_complete()')
        # enable adding new tabs
        self._tabwidget.enableButtonAdd(True)
        # update statusbar
        self._statusbar.set_world_load_progress('', -1)  # turn off progress display
        self.setStatusMessage(self.tr('World loaded.'))
        # update account info
        if self.overview_widget is not None:
            self.overview_widget.setEnabled(True)
            self.overview_widget.update_account_info()
            self.overview_widget.update_builds()
        # update flying fleets
        self.flights_widget.set_online_state(True)
        self.flights_widget.update_flights()
        # update planets
        planets = self.world.get_planets()
        self.setup_planets_panel(planets)
        if self.imperium_widget is not None:
            self.imperium_widget.setEnabled(True)
            self.imperium_widget.update_planets()
        # update statusbar
        self._statusbar.update_online_players_count()
        # update tray tooltip, add account name
        self.set_tray_tooltip(self.tr('XNova Commander') + ' - '
                              + self.world.get_account_info().login)
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
        self._statusbar.update_online_players_count()

    @pyqtSlot()
    def on_loaded_imperium(self):
        logger.debug('on_loaded_imperium')
        # need to update imperium widget
        if self.imperium_widget is not None:
            self.imperium_widget.update_planets()
        # the important note here is that imperium update is the only place where
        # the planets list is read, so number of planets, their names, etc may change here
        # Do we need to update planets panel also?
        self.update_planets_panel()

    @pyqtSlot()
    def on_world_timer(self):
        if self.world:
            self.world.world_tick()
        if self.flights_widget:
            self.flights_widget.update_flights()
        if self.overview_widget:
            self.overview_widget.update_builds()
        if self.imperium_widget:
            self.imperium_widget.update_planet_resources()

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

    @pyqtSlot()
    def on_show_settings(self):
        if self.settings_widget is not None:
            self.settings_widget.show()
            self.settings_widget.showNormal()

    @pyqtSlot(XNFlight)
    def on_flight_arrived(self, fl: XNFlight):
        logger.debug('main: flight arrival: {0}'.format(fl))
        mis_str = flight_mission_for_humans(fl.mission)
        if fl.direction == 'return':
            mis_str += ' ' + self.tr('return')
        short_fleet_info = self.tr('{0} {1} => {2}, {3} ship(s)').format(
            mis_str, fl.src, fl.dst, len(fl.ships))
        self.show_tray_message(self.tr('XNova: Fleet arrived'), short_fleet_info)

    @pyqtSlot(XNPlanet, XNPlanetBuildingItem)
    def on_building_complete(self, planet: XNPlanet, bitem: XNPlanetBuildingItem):
        logger.debug('main: build complete: on planet {0}: {1}'.format(
            planet.name, str(bitem)))
        if bitem.is_shipyard_item:
            binfo_str = '{0} x {1}'.format(bitem.quantity, bitem.name)
        else:
            binfo_str = self.tr('{0} lv.{1}').format(bitem.name, bitem.level)
        msg = self.tr('{0} has built {1}').format(planet.name, binfo_str)
        self.show_tray_message(self.tr('XNova: Building complete'), msg)

    @pyqtSlot(XNCoords)
    def on_request_open_galaxy_tab(self, coords: XNCoords):
        tab_index = self.find_tab_for_galaxy(coords.galaxy, coords.system)
        if tab_index == -1:  # create new tab for these coords
            self.add_tab_for_galaxy(coords)
            return
        # else switch to that tab
        self._tabwidget.setCurrentIndex(tab_index)

    @pyqtSlot(int)
    def on_request_open_planet_tab(self, planet_id: int):
        tab_index = self.find_tab_for_planet(planet_id)
        if tab_index == -1: # create new tab for planet
            planet = self.world.get_planet(planet_id)
            if planet is not None:
                self.add_tab_for_planet(planet)
                return
        # else switch to that tab
        self._tabwidget.setCurrentIndex(tab_index)

    def find_tab_for_planet(self, planet_id: int) -> int:
        """
        Finds tab index where specified planet is already opened
        :param planet_id: planet id to search for
        :return: tab index, or -1 if not found
        """
        cnt = self._tabwidget.count()
        if cnt < 3:
            return -1  # only overview and imperium tabs are present
        for index in range(2, cnt):
            tab_page = self._tabwidget.tabWidget(index)
            if tab_page is not None:
                try:
                    tab_type = tab_page.get_tab_type()
                    if tab_type == 'planet':
                        tab_planet = tab_page.planet()
                        if tab_planet.planet_id == planet_id:
                            # we have found tab index where this planet is already opened
                            return index
                except AttributeError:  # not all pages may have method get_tab_type()
                    pass
        return -1

    def find_tab_for_galaxy(self, galaxy: int, system: int) -> int:
        """
        Finds tab index where specified galaxy view is already opened
        :param galaxy: galaxy target coordinate
        :param system: system target coordinate
        :return: tab index, or -1 if not found
        """
        cnt = self._tabwidget.count()
        if cnt < 3:
            return -1  # only overview and imperium tabs are present
        for index in range(2, cnt):
            tab_page = self._tabwidget.tabWidget(index)
            if tab_page is not None:
                try:
                    tab_type = tab_page.get_tab_type()
                    if tab_type == 'galaxy':
                        coords = tab_page.coords()
                        if (coords[0] == galaxy) and (coords[1] == system):
                            # we have found galaxy tab index where this place is already opened
                            return index
                except AttributeError:  # not all pages may have method get_tab_type()
                    pass
        return -1

    def test_setup_planets_panel(self):
        """
        Testing only - add 'fictive' planets to test planets panel without loading data
        :return: None
        """
        pl1 = XNPlanet('Arnon', XNCoords(1, 7, 6))
        pl1.pic_url = 'skins/default/planeten/small/s_normaltempplanet08.jpg'
        pl1.fields_busy = 90
        pl1.fields_total = 167
        pl1.is_current = True
        pl2 = XNPlanet('Safizon', XNCoords(1, 232, 7))
        pl2.pic_url = 'skins/default/planeten/small/s_dschjungelplanet05.jpg'
        pl2.fields_busy = 84
        pl2.fields_total = 207
        pl2.is_current = False
        test_planets = [pl1, pl2]
        self.setup_planets_panel(test_planets)

    def test_planet_tab(self):
        """
        Testing only - add 'fictive' planet tab to test UI without loading world
        :return:
        """
        # construct planet
        pl1 = XNPlanet('Arnon', coords=XNCoords(1, 7, 6), planet_id=12345)
        pl1.pic_url = 'skins/default/planeten/small/s_normaltempplanet08.jpg'
        pl1.fields_busy = 90
        pl1.fields_total = 167
        pl1.is_current = True
        # add
        self.add_tab_for_planet(pl1)
