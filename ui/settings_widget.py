import configparser

from PyQt5.QtCore import pyqtSlot, Qt, QSize, QVariant
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
        # construct layout
        min_width = 150
        self.user_agents = dict()
        self.user_agents['chrome_win7_x64'] = ('Chrome 41, Windows 7 x64',
                                               'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                                               'Chrome/41.0.2227.0 Safari/537.36')
        self.user_agents['chrome_linux_64'] = ('Chrome 41, Linux x86_64',
                                               'Mozilla/5.0 (X11; Linux x86_64) '
                                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                                               'Chrome/41.0.2227.0 Safari/537.36')
        self.user_agents['chrome_android'] = ('Chrome 47, Android 4.3 Galaxy-S3',
                                              'Mozilla/5.0 (Linux; Android 4.3; GT-I9300 Build/JSS15J) '
                                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                                              'Chrome/47.0.2526.83 Mobile Safari/537.36')
        self.user_agents['firefox_win32'] = ('Firefox 40, Windows 7 32-bit',
                                             'Mozilla/5.0 (Windows NT 6.1; rv:40.0) '
                                             'Gecko/20100101 Firefox/40.1')
        self.user_agents['firefox_android'] = ('Firefox, Android 4.3 Galaxy-S3',
                                               'Mozilla/5.0 (Android 4.3; Mobile; rv:43.0) '
                                               'Gecko/43.0 Firefox/43.0')
        self.user_agents['edge_win10'] = ('Microsoft Edge, Windows 10 x64',
                                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                                          'Chrome/42.0.2311.135 Safari/537.36 Edge/12.246')
        # server URL
        self._l_surl = QHBoxLayout()
        self._l_ua = QHBoxLayout()
        self._lbl_surl = QLabel(self.tr('Server URL:'), self)
        self._lbl_surl.setMinimumWidth(min_width)
        self._le_surl = QLineEdit(self)
        self._l_surl.addWidget(self._lbl_surl)
        self._l_surl.addWidget(self._le_surl)
        self._layout.addLayout(self._l_surl)
        # emulate browser combo box
        self._l_eb = QHBoxLayout(self)
        self._lbl_eb = QLabel(self.tr('Emulate browser:'), self)
        self._lbl_eb.setMinimumWidth(min_width)
        self._cb_eb = QComboBox(self)
        self._cb_eb.setEditable(False)
        self._cb_eb.setInsertPolicy(QComboBox.InsertAtBottom)
        ua_keylist = [i for i in self.user_agents.keys()]
        ua_keylist.sort()
        for key_id in ua_keylist:
            b_tuple = self.user_agents[key_id]
            display_string = b_tuple[0]
            self._cb_eb.addItem(display_string, QVariant(str(key_id)))
        self._cb_eb.addItem(self.tr('<Custom>'), QVariant('custom'))
        self._l_eb.addWidget(self._lbl_eb)
        self._l_eb.addWidget(self._cb_eb)
        self._layout.addLayout(self._l_eb)
        # custom user-agent string
        self._lbl_ua = QLabel(self.tr('User-agent string:'), self)
        self._lbl_ua.setMinimumWidth(min_width)
        self._le_ua = QLineEdit(self)
        self._l_ua.addWidget(self._lbl_ua)
        self._l_ua.addWidget(self._le_ua)
        self._layout.addLayout(self._l_ua)
        # proxy settings
        self._l_proxy = QHBoxLayout()
        self._lbl_proxy = QLabel(self.tr('Proxy type:'), self)
        self._lbl_proxy.setMinimumWidth(min_width)
        self._cb_proxy = QComboBox(self)
        self._cb_proxy.setEditable(False)
        self._cb_proxy.addItem(self.tr('No proxy'), QVariant('none'))
        self._cb_proxy.addItem(self.tr('HTTP proxy'), QVariant('http'))
        self._cb_proxy.addItem(self.tr('SOCKS5 proxy'), QVariant('socks5'))
        self._l_proxy.addWidget(self._lbl_proxy)
        self._l_proxy.addWidget(self._cb_proxy)
        self._layout.addLayout(self._l_proxy)
        self._l_proxy_s = QHBoxLayout()
        self._lbl_proxy_s = QLabel(self.tr('Proxy addr:port:'), self)
        self._lbl_proxy_s.setMinimumWidth(min_width)
        self._le_proxy_addr = QLineEdit(self)
        self._l_proxy_s.addWidget(self._lbl_proxy_s)
        self._l_proxy_s.addWidget(self._le_proxy_addr)
        self._layout.addLayout(self._l_proxy_s)
        # all connections
        self._cb_eb.currentIndexChanged.connect(self.on_cb_eb_current_index_changed)
        self._cb_proxy.currentIndexChanged.connect(self.on_cb_proxy_current_index_changed)
        # finalize
        self._layout.addStretch()

    @pyqtSlot(int)
    def on_cb_eb_current_index_changed(self, index: int):
        key_id = str(self._cb_eb.currentData(Qt.UserRole))
        if key_id == 'custom':
            self._le_ua.setEnabled(True)
            return
        self._le_ua.setEnabled(False)
        if key_id in self.user_agents:
            b_tuple = self.user_agents[key_id]
            ua_str = b_tuple[1]
            self._le_ua.setText(ua_str)

    @pyqtSlot(int)
    def on_cb_proxy_current_index_changed(self, index: int):
        if index == 0:
            self._le_proxy_addr.setEnabled(False)
        else:
            self._le_proxy_addr.setEnabled(True)

    def ua_select(self, key_id: str):
        cnt = self._cb_eb.count()
        for i in range(cnt):
            item_key_id = str(self._cb_eb.itemData(i, Qt.UserRole))
            if item_key_id == key_id:
                self._cb_eb.setCurrentIndex(i)
                break

    def load_from_config(self, cfg: configparser.ConfigParser):
        # defaults
        xnova_url = 'uni4.xnova.su'
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        user_agent_id = 'custom'
        proxy = ''
        if 'net' in cfg:
            xnova_url = cfg['net']['xnova_url']
            user_agent = cfg['net']['user_agent']
            user_agent_id = cfg['net']['user_agent_id']
            proxy = cfg['net']['proxy']
        self._le_surl.setText(xnova_url)
        self._le_surl.setEnabled(False)  # cannot be edited by user, for safety!
        # deal with user-agent
        self._le_ua.setText(user_agent)
        if user_agent_id == 'custom':
            self._le_ua.setEnabled(True)
        else:
            self._le_ua.setEnabled(False)
        self.ua_select(user_agent_id)
        # deal with proxy
        if proxy == '':
            self._le_proxy_addr.setText('')
            self._cb_proxy.setCurrentIndex(0)
            self._le_proxy_addr.setEnabled(False)
        elif proxy.startswith('http://'):
            self._cb_proxy.setCurrentIndex(1)
            proxy_addr = proxy[7:]
            self._le_proxy_addr.setText(proxy_addr)
            self._le_proxy_addr.setEnabled(True)
        elif proxy.startswith('socks5://'):
            self._cb_proxy.setCurrentIndex(2)
            proxy_addr = proxy[9:]
            self._le_proxy_addr.setText(proxy_addr)
            self._le_proxy_addr.setEnabled(True)
        else:
            raise ValueError('Invalid proxy setting: ' + proxy)

    def save_to_config(self, cfg: configparser.ConfigParser):
        # ensure there is a 'net' section
        if 'net' not in cfg:
            cfg.add_section('net')
        # skip server url
        # deal with user-agent
        user_agent_id = ''
        user_agent = ''
        idx = self._cb_eb.currentIndex()
        if idx >= 0:
            user_agent_id = str(self._cb_eb.itemData(idx, Qt.UserRole))
            cfg['net']['user_agent_id'] = user_agent_id
        user_agent = self._le_ua.text().strip()
        if user_agent != '':
            cfg['net']['user_agent'] = user_agent
        # deal with proxy
        idx = self._cb_proxy.currentIndex()
        proxy_addr = self._le_proxy_addr.text().strip()
        if idx == 0:
            cfg['net']['proxy'] = ''
        elif idx == 1:
            cfg['net']['proxy'] = 'http://' + proxy_addr
        elif idx == 2:
            cfg['net']['proxy'] = 'socks5://' + proxy_addr
        logger.debug('Saved network config')


class Settings_Misc(QWidget):
    def __init__(self, parent: QWidget):
        super(Settings_Misc, self).__init__(parent)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        # label
        self._lbl = QLabel(self.tr('Misc'), self)
        # finalize layout
        self._layout.addWidget(self._lbl)
        self.hide()


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
        # network item
        lwi = QListWidgetItem()
        lwi.setText(self.tr('Network'))
        lwi.setTextAlignment(Qt.AlignCenter)
        lwi.setIcon(QIcon(':/i/settings_network_32.png'))
        lwi.setData(Qt.UserRole, QVariant(0))
        self._sections_list.addItem(lwi)
        lwi.setSelected(True)
        # misc item
        lwi = QListWidgetItem()
        lwi.setText(self.tr('Other'))
        lwi.setTextAlignment(Qt.AlignCenter)
        lwi.setIcon(QIcon(':/i/settings_32.png'))
        lwi.setData(Qt.UserRole, QVariant(1))
        self._sections_list.addItem(lwi)
        # connections
        self._sections_list.currentItemChanged.connect(self.on_section_current_item_changed)
        self._layout_stacks.addWidget(self._sections_list)
        # stacked widget
        self._stack = QStackedWidget(self)
        self._w_net = Settings_Net(self._stack)
        self._w_misc = Settings_Misc(self._stack)
        self._stack.addWidget(self._w_net)
        self._stack.addWidget(self._w_misc)
        self._stack.setCurrentIndex(0)
        self._layout_stacks.addWidget(self._stack)
        # ok cancel buttons
        self._btn_ok = QPushButton(self)
        self._btn_ok.setText(self.tr('Save'))
        self._btn_ok.setIcon(QIcon(':/i/save.png'))
        self._btn_cancel = QPushButton(self)
        self._btn_cancel.setText(self.tr('Cancel'))
        self._btn_cancel.setIcon(QIcon(':/i/cancel.png'))
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
        self._cfg.read('config/net.ini', encoding='utf-8')
        # init config of all child widgets
        self._w_net.load_from_config(self._cfg)

    def save_settings(self):
        # read config from all child widgets
        self._w_net.save_to_config(self._cfg)
        # save to file
        try:
            with open('config/net.ini', 'wt', encoding='utf-8') as fp:
                self._cfg.write(fp)
                fp.write('# proxy Tor example (local Tor browser):\n')
                fp.write('# proxy = socks5://127.0.0.1:9050\n')
                fp.write('# proxy I2P example:\n')
                fp.write('# proxy = http://127.0.0.1:4444\n')
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
        data = int(cur.data(Qt.UserRole))
        self._stack.setCurrentIndex(data)
