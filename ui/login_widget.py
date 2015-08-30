import re
import pickle
import configparser

import requests
import requests.exceptions

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QUrl, QThread
from PyQt5.QtGui import QDesktopServices, QMovie

from xnova import xn_logger

logger = xn_logger.get(__name__, debug=False)


# background network operations for login widget
class LoginThread(QThread):
    def __init__(self, parent=None):
        super(LoginThread, self).__init__(parent)
        # state vars
        self.xnova_url = 'uni4.xnova.su'
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.email = ''
        self.password = ''
        self.remember = False
        self.step = 1
        self.error_msg = ''
        self.login_ok = False
        # load settings from config/net.ini
        cfg = configparser.ConfigParser()
        cfg.read('config/net.ini', encoding='utf-8')
        if 'net' in cfg:
            self.user_agent = cfg['net']['user_agent']
            self.xnova_url = cfg['net']['xnova_url']
        # construct requests HTTP session
        self.sess = requests.Session()
        self.sess.headers.update({'user-agent': self.user_agent})
        self.requests_cookiejar = None

    # overrides QThread.run()
    def run(self):
        if self.step == 1:
            self.run_step1()
        if self.step == 2:
            self.run_step2()

    def set_error(self, msg):
        self.step = 1
        self.error_msg = msg
        self.login_ok = False

    def run_step1(self):
        self.error_msg = ''
        logger.debug('NetThread: step 1, loading auth page')
        try:
            url = 'http://{0}/'.format(self.xnova_url)
            r = self.sess.get(url)
            if r.status_code == requests.codes.ok:
                logger.debug('Loaded login page OK')
                self.step += 1
            else:
                logger.debug('Unexpected response code: HTTP {0}'.format(r.status_code))
                self.set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.debug('Exception {0}'.format(type(e)))
            self.set_error(str(e))

    def run_step2(self):
        logger.debug('NetThread: step 2, sending auth')
        try:
            # emails=minlexx%40mail.ru&password=wwwvadv&rememberme=on
            postdata = {'emails': self.email, 'password': self.password}
            if self.remember:
                postdata['rememberme'] = 'on'
            headers = {'referer': 'http://{0}/'.format(self.xnova_url),
                       'X-Requested-With': 'XMLHttpRequest'}
            url = 'http://{0}/?set=login&xd&popup&ajax'.format(self.xnova_url)
            r = self.sess.post(url, data=postdata, headers=headers)
            # http://uni4.xnova.su/?set=login&xd&popup&ajax
            if r.status_code == requests.codes.ok:
                logger.debug('Loaded auth response page OK')
                logger.debug(r.text)
                # success: '<script>top.location.href="?set=overview";</script>'
                self.step += 1
                match = re.search('^<script', r.text)
                if match:
                    self.login_ok = True
                    self.requests_cookiejar = self.sess.cookies
                else:
                    self.set_error(r.text)
            else:
                logger.debug('Unexpected response code: HTTP {0}'.format(r.status_code))
                self.set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.debug('Exception {0}'.format(type(e)))
            self.set_error(str(e))

    def run_step3(self):
        self.step = 1


# Manages all login process
class LoginWidget(QWidget):
    # signals
    loginOk = pyqtSignal(str, dict)  # (login(email), cookies{})
    loginError = pyqtSignal(str)

    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)
        self.uifile = 'ui/login_widget.ui'
        self.pickle_filename = 'cache/login.dat'
        self.xnova_url = 'uni4.xnova.su'
        self.ui = None
        self.loading_gif = None
        # thread for network operations
        self.th = None

    def load_ui(self):
        self.ui = uic.loadUi(self.uifile, self)
        self.ui.lbl_loading.hide()
        self.ui.btn_login.clicked.connect(self.on_btn_login)
        self.ui.btn_register.clicked.connect(self.on_btn_register)
        self.loading_gif = QMovie(':/i/loading.gif')
        self.restore_login()
        # load xnova url from config/net.ini
        cfg = configparser.ConfigParser()
        cfg.read('config/net.ini', encoding='utf-8')
        if 'net' in cfg:
            self.xnova_url = cfg['net']['xnova_url']

    def save_login(self):
        email = self.ui.le_email.text()
        password = self.ui.le_pass.text()
        remember = self.ui.chk_remember.isChecked()
        auth_data = (email, password, remember)
        try:
            with open(self.pickle_filename, 'wb') as f:
                pickle.dump(auth_data, f)
        except pickle.PickleError as pe:
            pass
        except IOError as ioe:
            pass

    def restore_login(self):
        try:
            with open(self.pickle_filename, 'rb') as f:
                auth_data = pickle.load(f)
                self.ui.le_email.setText(auth_data[0])
                self.ui.le_pass.setText(auth_data[1])
                if auth_data[2]:
                    self.ui.chk_remember.setChecked(True)
                else:
                    self.ui.chk_remember.setChecked(False)
        except pickle.PickleError as pe:
            pass
        except IOError as ioe:
            pass

    @pyqtSlot()
    def on_btn_register(self):
        logger.debug('register clicked, opening [http://{0}/]'.format(self.xnova_url))
        QDesktopServices.openUrl(QUrl('http://{0}/'.format(self.xnova_url)))

    @pyqtSlot()
    def on_btn_login(self):
        logger.debug('login clicked')
        self.ui.btn_login.hide()
        self.ui.btn_register.hide()
        self.ui.le_email.setEnabled(False)
        self.ui.le_pass.setEnabled(False)
        self.ui.chk_remember.setEnabled(False)
        self.ui.lbl_loading.show()
        self.ui.lbl_loading.setMovie(self.loading_gif)
        self.loading_gif.start()
        if self.ui.chk_remember.isChecked():
            self.save_login()
        # create thread object
        self.th = LoginThread(self)
        self.th.finished.connect(self.on_thread_finished)
        # get form data and start thread
        self.th.email = self.ui.le_email.text()
        self.th.password = self.ui.le_pass.text()
        self.th.remember = self.ui.chk_remember.isChecked()
        self.th.start()

    @pyqtSlot()
    def on_thread_finished(self):
        logger.debug('thread finished')
        self.loading_gif.stop()
        self.ui.le_email.setEnabled(True)
        self.ui.le_pass.setEnabled(True)
        self.ui.chk_remember.setEnabled(True)
        self.ui.btn_login.show()
        self.ui.btn_register.show()
        self.ui.lbl_loading.hide()
        if self.th.login_ok:
            logger.info('Login ({0}) ok'.format(self.th.email))
            cookies_dict = self.th.requests_cookiejar.get_dict()
            # logger.debug(cookies_dict)
            # emit signal
            self.loginOk.emit(self.th.email, cookies_dict)
        else:
            logger.error('Login error: {0}'.format(self.th.error_msg))
            self.loginError.emit(self.th.error_msg)
        self.th = None
