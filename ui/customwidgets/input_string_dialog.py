from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog, QWidget, QPushButton, QLabel, \
    QVBoxLayout, QHBoxLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QIcon

from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class InputStringDialog(QDialog):
    def __init__(self, parent: QWidget=None):
        super(InputStringDialog, self).__init__(parent)
        self._value = ''
        # layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self._hlayout1 = QHBoxLayout()
        self._hlayout2 = QHBoxLayout()
        # input controls
        self._lbl_prompt = QLabel(self)
        self._le_text = QLineEdit(self)
        # buttons
        # self._btn_ok = QPushButton(self.tr('OK'), self)
        # self._btn_cancel = QPushButton(self.tr('Cancel'), self)
        self._btnbox = QDialogButtonBox(self)
        self._btnbox.addButton(QDialogButtonBox.Ok)
        self._btnbox.addButton(QDialogButtonBox.Cancel)
        self._btnbox.accepted.connect(self.on_ok)
        self._btnbox.rejected.connect(self.on_cancel)
        #
        # finalize layout
        self._hlayout1.addWidget(self._lbl_prompt)
        self._hlayout1.addWidget(self._le_text)
        self._hlayout2.addWidget(self._btnbox)
        self._layout.addLayout(self._hlayout1)
        self._layout.addLayout(self._hlayout2)

    def value(self) -> str:
        return self._value

    def setValue(self, v: str):
        self._value = v
        self._le_text.setText(self._value)

    def setPrompt(self, p: str):
        self._lbl_prompt.setText(p)

    @pyqtSlot()
    def on_ok(self):
        self._value = self._le_text.text()
        self.accept()

    @pyqtSlot()
    def on_cancel(self):
        self.reject()


def input_string_dialog(parent: QWidget, window_title: str, prompt: str, value: str=None) -> str:
    ret = None
    dlg = InputStringDialog(parent)
    dlg.setWindowTitle(window_title)
    dlg.setPrompt(prompt)
    if value is not None:
        dlg.setValue(value)
    if dlg.exec_() == QDialog.Accepted:
        ret = dlg.value()
    return ret
