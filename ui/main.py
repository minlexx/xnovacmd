from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QMessageBox, QSystemTrayIcon
from PyQt5.QtGui import QIcon, QCloseEvent
from PyQt5 import uic

from .login_widget import LoginWidget
from .overview import OverviewWidget

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


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
        self.login_widget = None
        self.overview_widget = None
        # initialization
        self.load_ui()

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        if QSystemTrayIcon.isSystemTrayAvailable():
            logger.debug('System tray icon is available, showing')
            self.tray_icon = QSystemTrayIcon(QIcon(':/i/favicon_16.png'), self)
            self.tray_icon.setToolTip('XNova Commander')
            self.tray_icon.show()

    def closeEvent(self, close_event:QCloseEvent):
        logger.debug('closing')
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon =  None
        close_event.accept()

    def add_tab(self, widget, tab_name):
        tab_index = self.ui.tabWidget.addTab(widget, tab_name)
        widget.show()

    def begin_login(self):
        self.login_widget = LoginWidget(self.ui.tabWidget)
        self.login_widget.load_ui()
        self.login_widget.loginError.connect(self.on_login_error)
        self.login_widget.loginOk.connect(self.on_login_ok)
        self.add_tab(self.login_widget, 'Login')

    @pyqtSlot(str)
    def on_login_error(self, errstr):
        logger.error('Login error: {0}'.format(errstr))
        self.state = self.STATE_NOT_AUTHED
        QMessageBox.critical(self, 'Login error:', errstr)

    @pyqtSlot(dict)
    def on_login_ok(self, login_email, cookies_dict):
        logger.debug('Login OK, login: {0}, cookies: {1}'.format(login_email, str(cookies_dict)))
        # save login data: email, cookies
        self.state = self.STATE_AUTHED
        self.login_email = login_email
        self.cookies_dict = cookies_dict
        # destroy login widget
        self.ui.tabWidget.removeTab(0)
        self.login_widget = None
        # create all main widgets
        # overview widget
        self.overview_widget = OverviewWidget(self)
        #self.overview_widget.load_ui()
        self.add_tab(self.overview_widget, 'Overview')
