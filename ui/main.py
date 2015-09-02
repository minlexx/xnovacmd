from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QMessageBox, QSystemTrayIcon, QBoxLayout
from PyQt5.QtGui import QIcon, QCloseEvent

from .statusbar import XNCStatusBar
from .login_widget import LoginWidget
from .flights_widget import FlightsWidget
from .overview import OverviewWidget

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
        self.state = self.STATE_NOT_AUTHED
        self.login_email = ''
        self.cookies_dict = {}
        # objects, sub-windows
        self.ui = None
        self.tray_icon = None
        self.statusbar = None
        self.login_widget = None
        self.overview_widget = None
        self.flights_widget = None
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
            self.tray_icon.setToolTip('XNova Commander')
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            self.tray_icon.show()
        # create status bar
        self.statusbar = XNCStatusBar(self)
        self.layout().addWidget(self.statusbar)
        self.statusbar.setupUi()
        self.setStatusMessage('Not authorized, not connected: Log in!')

    # overrides QWidget.closeEvent
    # cleanup just before the window close
    def closeEvent(self, close_event: QCloseEvent):
        logger.debug('closing')
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon =  None
        if self.world_timer.isActive():
            self.world_timer.stop()
        if self.world.isRunning():
            self.world.quit()
            logger.debug('waiting for world thread to stop (5 sec)...')
            wait_res = self.world.wait(5000)
            if not wait_res:
                logger.warn('wait failed, last chance, terminating!')
                self.world.terminate()
        close_event.accept()

    def setStatusMessage(self, msg: str):
        self.statusbar.setStatus(msg)

    # convenient internal wrapper
    def add_tab(self, widget, tab_name):
        tab_index = self.ui.tabWidget.addTab(widget, tab_name)
        widget.show()

    # defaults:
    # orientation = Qt.Vertical
    # margins = (11, 11, 11, 11)  # from Qt docs, style dependent
    def install_layout_for_widget(self, widget, orientation=None, margins=None, spacing=None):
        if widget.layout():
            return  # already has a layout
        direction = QBoxLayout.TopToBottom
        if orientation == Qt.Horizontal:
            direction = QBoxLayout.LeftToRight
        l = QBoxLayout(direction)
        if margins:
            l.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        if spacing:
            l.setSpacing(spacing)
        widget.setLayout(l)

    # called by main application object just after main window creation
    # to show login widget and begin login process
    def begin_login(self):
        # create and show login widget as first tab
        self.login_widget = LoginWidget(self.ui.tabWidget)
        self.login_widget.load_ui()
        self.login_widget.loginError.connect(self.on_login_error)
        self.login_widget.loginOk.connect(self.on_login_ok)
        self.add_tab(self.login_widget, 'Login')

    @pyqtSlot(str)
    def on_login_error(self, errstr):
        logger.error('Login error: {0}'.format(errstr))
        self.state = self.STATE_NOT_AUTHED
        self.setStatusMessage('Login error: {0}'.format(errstr))
        QMessageBox.critical(self, 'Login error:', errstr)

    @pyqtSlot(str, dict)
    def on_login_ok(self, login_email, cookies_dict):
        logger.debug('Login OK, login: {0}, cookies: {1}'.format(login_email, str(cookies_dict)))
        # save login data: email, cookies
        self.state = self.STATE_AUTHED
        self.setStatusMessage('Login OK, loading world')
        self.login_email = login_email
        self.cookies_dict = cookies_dict
        # destroy login widget and remove its tab
        self.ui.tabWidget.removeTab(0)
        self.login_widget = None
        # create all main widgets
        # create flights widget
        self.flights_widget = FlightsWidget(self)
        self.flights_widget.load_ui()
        self.install_layout_for_widget(self.ui.fr_flights, Qt.Vertical, margins=(1,1,1,1), spacing=1)
        self.ui.fr_flights.layout().addWidget(self.flights_widget)
        # create overview widget and add it as first tab
        self.overview_widget = OverviewWidget(self)
        self.overview_widget.load_ui()
        self.add_tab(self.overview_widget, 'Overview')
        self.overview_widget.setEnabled(False)
        # initialize XNova world updater
        self.world.parser_overview.account.email = self.login_email
        self.world.initialize(cookies_dict)
        self.world.world_load_complete.connect(self.on_world_load_complete)
        self.world.start()

    @pyqtSlot()
    def on_world_load_complete(self):
        logger.debug('main: on_world_load_complete()')
        self.setStatusMessage('World loaded.')
        # update account info
        self.overview_widget.setEnabled(True)
        self.overview_widget.update_account_info()
        # update flying fleets
        self.flights_widget.update_flights()
        # set timer to do every-second world recalculation
        self.world_timer.setInterval(1000)
        self.world_timer.setSingleShot(False)
        self.world_timer.start()

    @pyqtSlot()
    def on_world_timer(self):
        if self.world:
            self.world.world_tick()
        if self.flights_widget:
            self.flights_widget.flights_tick()

    @pyqtSlot(int)
    def on_tray_icon_activated(self, reason):
        # QSystemTrayIcon::Unknown	0	Unknown reason
        # QSystemTrayIcon::Context	1	The context menu for the system tray entry was requested
        # QSystemTrayIcon::DoubleClick	2	The system tray entry was double clicked
        # QSystemTrayIcon::Trigger	3	The system tray entry was clicked
        # QSystemTrayIcon::MiddleClick	4	The system tray entry was clicked with the middle mouse button
        if reason == QSystemTrayIcon.Trigger:
            # left-click
            self.setWindowState( (self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            self.show()
            return

    def show_tray_message(self, title, message, icon_type=None, timeout_ms=None):
        """
        Shows message from system tray icon
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
            logger.debug('This system does not support tray icon messages.')
