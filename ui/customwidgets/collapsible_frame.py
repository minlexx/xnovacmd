# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFrame, QToolButton, QVBoxLayout, QLayout

from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class CollapsibleFrame(QFrame):
    def __init__(self, parent: QWidget = None):
        # Constructs a frame widget with frame style NoFrame and a 1-pixel frame width.
        super(CollapsibleFrame, self).__init__(parent)
        # possible values are:
        #   QFrame.NoFrame, QFrame.Box, QFrame.Panel, QFrame.StyledPanel,
        #   QFrame.HLine, QFrame.VLine, QFrame.WinPanel
        self.setFrameShape(QFrame.Box)
        # possible values are:  QFrame.Plain, QFrame.Raised, QFrame.Sunken
        self.setFrameShadow(QFrame.Plain)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(1)
        self.setLayout(self._layout)
        # button
        self._button = QToolButton(self)
        self._button.setArrowType(Qt.RightArrow)
        self._button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._button.setAutoRaise(False)
        self._button.setText('CollapsibleFrame')
        self._layout.addWidget(self._button)
        self._button.setVisible(True)
        # group box
        self._panel = QWidget(self)
        self._layout.addWidget(self._panel)
        self._panel.setVisible(False)
        # connect signals
        self._button.clicked.connect(self.on_button_click)
        # private state variables
        self._is_collapsed = True

    def setTitle(self, title: str):
        self._button.setText(title)

    def setInternalLayout(self, layout):
        self._panel.setLayout(layout)

    def internalLayout(self) -> QLayout:
        return self._panel.layout()

    @pyqtSlot()
    def on_button_click(self):
        logger.debug('button clicked')
        if self._is_collapsed:
            self._panel.setVisible(True)
            self._button.setArrowType(Qt.DownArrow)
            self._is_collapsed = False
            return
        else:
            self._panel.setVisible(False)
            self._button.setArrowType(Qt.RightArrow)
            self._is_collapsed = True
            return
