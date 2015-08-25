import sys
from PyQt5.QtCore import PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication

from ui import xn_logger
from ui.main import XNova_MainWindow
import ui.res_rc

g_app = None
logger = xn_logger.get('app.main')


class MyApplication(QApplication):
    def __init__(self, argv):
        super(MyApplication, self).__init__(argv)
        # main window
        self.mainwindow = XNova_MainWindow()
        self.mainwindow.show()
        self.mainwindow.begin_login()


if __name__ == '__main__':
    logger.info('XNova Commander starting, using PyQt v{0}'.format(PYQT_VERSION_STR))
    g_app = MyApplication(sys.argv)
    retcode = 0
    try:
        retcode = g_app.exec_()
    except Exception as e:
        print(e)
        retcode = 1
    sys.exit(retcode)
