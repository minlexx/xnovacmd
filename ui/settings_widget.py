import configparser

from PyQt5.QtCore import pyqtSlot, Qt, QSize
from PyQt5.QtWidgets import QWidget, QStackedWidget, QPushButton, QLineEdit, QLabel, \
    QVBoxLayout, QHBoxLayout, QComboBox, QGroupBox, QListWidget, QListView, \
    QAbstractItemView, QListWidgetItem
from PyQt5.QtGui import QIcon

from ui.xnova import xn_logger


logger = xn_logger.get(__name__, debug=True)


class Settings_Net(QWidget):
    def __init__(self, parent: QWidget):
        super(Settings_Net, self).__init__(parent)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        #
        self._l_surl = QHBoxLayout()
        self._lbl_surl = QLabel(self)
        self._lbl_surl.setText(self.tr('Server URL:'))
        self._le_surl = QLineEdit(self)
        self._l_surl.addWidget(self._lbl_surl)
        self._l_surl.addWidget(self._le_surl)
        self._layout.addLayout(self._l_surl)


class SettingsWidget(QWidget):
    def __init__(self, parent: QWidget):
        super(SettingsWidget, self).__init__(parent, Qt.Window)
        # config parser
        self._cfg = configparser.ConfigParser()
        # layouts
        self._layout_main = QVBoxLayout()
        self._layout_stacks = QHBoxLayout()
        self._layout_okcancel = QHBoxLayout()
        # sections list
        self._sections_list = QListWidget(self)
        self._sections_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._sections_list.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._sections_list.setIconSize(QSize(32, 32))
        self._sections_list.setViewMode(QListView.IconMode)
        self._sections_list.setMaximumWidth(80)
        self._sections_list.setGridSize(QSize(64, 64))
        self._sections_list.setFlow(QListView.TopToBottom)
        self._sections_list.setMovement(QListView.Static)  # items cannot be moved by user
        lwi = QListWidgetItem()
        lwi.setText(self.tr('Network'))
        lwi.setTextAlignment(Qt.AlignCenter)
        lwi.setIcon(QIcon(':/i/settings_network_32.png'))
        self._sections_list.addItem(lwi)
        lwi.setSelected(True)
        self._sections_list.currentItemChanged.connect(self.on_section_current_item_changed)
        self._sections_list.itemSelectionChanged.connect(self.on_section_selection_changed)
        self._layout_stacks.addWidget(self._sections_list)
        # stacked widget
        self._stack = QStackedWidget(self)
        self._w_net = Settings_Net(self._stack)
        self._stack.addWidget(self._w_net)
        self._stack.setCurrentIndex(0)
        self._layout_stacks.addWidget(self._stack)
        # ok cancel buttons
        self._btn_ok = QPushButton(self)
        self._btn_ok.setText(self.tr('Save'))
        self._btn_cancel = QPushButton(self)
        self._btn_cancel.setText(self.tr('Cancel'))
        self._layout_okcancel.addStretch()
        self._layout_okcancel.addWidget(self._btn_ok)
        self._layout_okcancel.addWidget(self._btn_cancel)
        self._btn_ok.clicked.connect(self.on_ok)
        self._btn_cancel.clicked.connect(self.on_cancel)
        # final
        self._layout_main.addLayout(self._layout_stacks)
        self._layout_main.addLayout(self._layout_okcancel)
        self.setLayout(self._layout_main)
        self.setWindowTitle(self.tr('Settings'))
        self.setWindowIcon(QIcon(':/i/settings_32.png'))
        #
        self.load_settings()

    def load_settings(self):
        logger.debug('load settings')
        self._cfg.read('config/net.ini', encoding='utf-8')
        pass

    def save_settings(self):
        logger.debug('save settings')
        try:
            with open('config/new.ini', 'wt', encoding='utf-8') as fp:
                self._cfg.write(fp)
        except IOError as e:
            logger.error(str(e))

    @pyqtSlot()
    def on_ok(self):
        self.save_settings()
        self.hide()

    def on_cancel(self):
        self.hide()

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_section_current_item_changed(self, cur: QListWidgetItem, prev: QListWidgetItem):
        logger.debug('on_section_current_item_changed')
        pass

    @pyqtSlot()
    def on_section_selection_changed(self):
        logger.debug('on_section_selection_changed')
        pass

