# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFrame, QToolButton, QVBoxLayout, QLayout, QSizePolicy

from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=False)


class CollapsibleFrame(QFrame):

    expanded = pyqtSignal()
    collapsed = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        # Constructs a frame widget with frame style NoFrame and a 1-pixel frame width.
        super(CollapsibleFrame, self).__init__(parent)
        # possible values are:
        #   QFrame.NoFrame, QFrame.Box, QFrame.Panel, QFrame.StyledPanel,
        #   QFrame.HLine, QFrame.VLine, QFrame.WinPanel
        self.setFrameShape(QFrame.StyledPanel)
        # possible values are:  QFrame.Plain, QFrame.Raised, QFrame.Sunken
        self.setFrameShadow(QFrame.Plain)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)
        # button
        self._button = QToolButton(self)
        self._button.setArrowType(Qt.RightArrow)
        self._button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._button.setAutoRaise(False)
        self._button.setText('CollapsibleFrame')
        self._button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._layout.addWidget(self._button, 0)
        self._button.setVisible(True)
        # group box
        self._panel = QWidget(self)
        self._layout.addWidget(self._panel)
        self._panel.setVisible(False)
        self._panel_layout = QVBoxLayout()
        self._panel_layout.setContentsMargins(1, 1, 1, 1)
        self._panel_layout.setSpacing(2)
        self._panel.setLayout(self._panel_layout)
        # connect signals
        self._button.clicked.connect(self.on_button_click)
        # private state variables
        self._is_collapsed = True

    def setTitle(self, title: str):
        self._button.setText(title)

    def addWidget(self, widget: QWidget):
        self._panel_layout.addWidget(widget)

    def removeWidget(self, widget: QWidget):
        self._panel_layout.removeWidget(widget)

    def is_expanded(self) -> bool:
        return not self._is_collapsed

    def expand(self):
        self._button.setArrowType(Qt.DownArrow)
        self._panel.setVisible(True)
        self._is_collapsed = False
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

    def collapse(self):
        self._panel.setVisible(False)
        self._button.setArrowType(Qt.RightArrow)
        self._is_collapsed = True
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    @pyqtSlot()
    def on_button_click(self):
        if self._is_collapsed:
            self.expand()
            self.expanded.emit()
            return
        else:
            self.collapse()
            self.collapsed.emit()
            return
