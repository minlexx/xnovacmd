#!/usr/bin/python3

"""
Entry point to application.

Python modules used by application in whole:
- PyQt5
- requests
- PyExecJS
- PySocks for SOCKS5 proxy socket, required by requesocks
- certifi for HTTPS certificate validation, also used in depths of requesocks
- requesocks is included in source tree
"""

import sys

import sip
from PyQt5.QtCore import PYQT_VERSION_STR, QTranslator, QLocale
from PyQt5.QtWidgets import QApplication

from ui.xnova import xn_logger
from ui.main import XNova_MainWindow

# we need to import this file to initialize all Qt compiled resources
import ui.res_rc

logger = xn_logger.get(__name__)


# Main application class
class MyApplication(QApplication):
    def __init__(self, argv):
        super(MyApplication, self).__init__(argv)
        self.mainwindow = None

    def setup_translation(self):
        self.tr("Test translator")
        sys_locale = QLocale.system()
        lang_code = QLocale.languageToString(sys_locale.language())
        logger.info('System language: {0}, {1}'.format(lang_code, sys_locale.bcp47Name()))
        translator = QTranslator(self)
        # bool load(locale, filename, prefix = '', directory = '', suffix = '')
        res = translator.load(sys_locale, 'xnovacmd', '_', './translations')
        # Loads filename + prefix + ui language name + suffix (".qm" if the suffix is not specified),
        # which may be an absolute file name or relative to directory.
        # Returns true if the translation is successfully loaded; otherwise returns false.
        if res:
            logger.info('Loaded translation OK')
            self.installTranslator(translator)
        else:
            logger.warn('Failed to load translator!')

    def create_window(self):
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
    # fix PyQt crashes during program exit?
    sip.setdestroyonexit(False)
    # create global application object
    # and keep reference to it to prevent garbage collection
    app = MyApplication(sys.argv)
    app.setApplicationName('xnovacmd')
    app.setApplicationVersion('0.1')
    app.setApplicationDisplayName('XNova Commander')
    app.setup_translation()
    app.create_window()
    xn_logger.handle_unhandled(True)
    retcode = app.exec_()  # Qt event loop!
    app.mainwindow.close()
    app.mainwindow = None
    xn_logger.handle_unhandled(False)
    logger.info('Application exiting with code {0}'.format(retcode))
    sys.exit(retcode)
