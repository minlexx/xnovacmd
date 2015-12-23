import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QStatusBar, QPushButton, QProgressBar, QLabel, QAction, QMenu
from PyQt5.QtGui import QCursor, QMovie

from .xnova.xn_world import XNovaWorld_instance
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class XNCStatusBar(QStatusBar):

    def __init__(self, parent=None):
        super(XNCStatusBar, self).__init__(parent)
        # state vars
        self.world = XNovaWorld_instance()
        # initialization
        self.setSizeGripEnabled(True)
        # sub-widgets
        # progressbar
        self._progressbar = QProgressBar(self)
        self._progressbar.hide()
        self._progressbar.setValue(0)
        self._progressbar.setRange(0, 99)
        # online players counter
        self._lbl_online = QLabel(self.tr('Online') + ': 0', self)
        # label with loading.gif
        self._loading_gif = QMovie(':/i/loading.gif')
        self._lbl_loading = QLabel(self)
        self._lbl_loading.setMovie(self._loading_gif)
        self._lbl_loading.hide()
        # testing only
        self._btn_runscript = QPushButton('Run script', self)
        self._btn_runscript.clicked.connect(self.on_run_script)
        self.addPermanentWidget(self._btn_runscript)
        #
        self.addPermanentWidget(self._lbl_loading)
        self.addPermanentWidget(self._lbl_online)  # should be las right widget
        self.show()

    def set_status(self, msg: str, timeout: int=0):
        self.showMessage(msg, timeout)

    def set_loading_status(self, loading: bool):
        if loading:
            self._lbl_loading.show()
            self._loading_gif.start()
        else:
            self._loading_gif.stop()
            self._lbl_loading.hide()

    def set_world_load_progress(self, comment: str, progress: int):
        """
        Display world load progress in status bar
        :param comment: string comment of what is currently loading
        :param progress: percent progress, or -1 to disable
        """
        if progress != -1:
            if not self._progressbar.isVisible():
                self.insertPermanentWidget(0, self._progressbar)
                self._progressbar.show()
            msg = self.tr('Loading world') + ' ({0}%) {1}...'.format(progress, comment)
            logger.debug(msg)
            self._progressbar.setValue(progress)
            self.set_status(msg)
        else:
            self.removeWidget(self._progressbar)
            self._progressbar.hide()
            self._progressbar.reset()
            self.clearMessage()

    def update_online_players_count(self):
        op = self.world.get_online_players()
        self._lbl_online.setText(self.tr('Online') + ': {0}'.format(op))

# some functions may be useful, documentation:
# void QStatusBar::clearMessage()
# void QStatusBar::addPermanentWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::addWidget(QWidget * widget, int stretch = 0)
# void QStatusBar::removeWidget(QWidget * widget)

    @pyqtSlot()
    def on_run_script(self):
        files = os.listdir('scripts')
        files.sort()
        script_files = [fn for fn in files if fn[0] != '.' and fn.endswith('.py')]
        # print(script_files)
        menu = QMenu(self)
        for script_filename in script_files:
            act = QAction(menu)
            act.setText('Run "scripts/' + script_filename + '"...')
            act.setData('scripts/' + script_filename)
            menu.addAction(act)
        act_ret = menu.exec(QCursor.pos())
        if act_ret is None:
            return
        script_filename = str(act_ret.data())
        s = ''
        try:
            with open(script_filename, 'rt', encoding='utf-8') as f:
                s = f.read()
        except IOError:
            pass
        if s != '':
            exec(s)
