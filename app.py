#!/usr/bin/python3
import sys

from PyQt5.QtCore import PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication

from ui.xnova import xn_logger
from ui.main import XNova_MainWindow

# we need to import this file to initialize all Qt compiled resources
import ui.res_rc

g_app = None
logger = xn_logger.get(__name__)


# Main application class
class MyApplication(QApplication):
    def __init__(self, argv):
        super(MyApplication, self).__init__(argv)
        # create main window and keep reference to it
        self.mainwindow = XNova_MainWindow()
        self.mainwindow.show()
        # switch phase to login, show login widget and begin login process
        self.mainwindow.begin_login()


if __name__ == '__main__':
    logger.info('XNova Commander starting, using PyQt v{0}'.format(PYQT_VERSION_STR))
    # next is not really needed, because it is called at import time
    # bui I need to silence PyCharm about unused import!!!
    ui.res_rc.qInitResources()
    # create global application object
    g_app = MyApplication(sys.argv)
    # keep reference to it to prevent garbage collection
    xn_logger.handle_unhandled(True)
    retcode = g_app.exec_()  # Qt event loop!
    xn_logger.handle_unhandled(False)
    logger.info('Application exiting with code {0}'.format(retcode))
    del g_app  # free reference - now can be garbage collected
    sys.exit(retcode)
