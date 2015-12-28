from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QRect, QSize
from PyQt5.QtWidgets import QWidget, QFrame, QStackedWidget, QTabBar, \
    QVBoxLayout, QHBoxLayout, QPushButton

from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class XTabWidget(QFrame):

    addClicked = pyqtSignal()
    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)

    def __init__(self, QWidget_parent=None):
        super(XTabWidget, self).__init__(QWidget_parent)
        # setup self frame
        self.setFrameShadow(QFrame.Raised)
        # self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShape(QFrame.NoFrame)
        # layouts
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._layout_top = QHBoxLayout()
        self._layout_top.setContentsMargins(0, 0, 0, 0)
        # stacked widget
        self._stack = QStackedWidget(self)
        # tab bar
        self._tabbar = QTabBar(self)
        self._tabbar.setTabsClosable(True)
        self._tabbar.setMovable(False)
        self._tabbar.setExpanding(False)
        self._tabbar.setShape(QTabBar.RoundedNorth)
        self._tabbar.currentChanged.connect(self.on_tab_current_changed)
        self._tabbar.tabCloseRequested.connect(self.on_tab_close_requested)
        # button "add"
        self._btn_add = QPushButton('+', self)
        self._btn_add.setMaximumSize(QSize(22, 22))
        self._btn_add.clicked.connect(self.on_btn_add_clicked)
        # complete layout
        self._layout_top.addWidget(self._btn_add, 0, Qt.AlignVCenter)
        self._layout_top.addWidget(self._tabbar, 1, Qt.AlignVCenter)
        self._layout.addLayout(self._layout_top)
        self._layout.addWidget(self._stack)
        self.setLayout(self._layout)

    def addTab(self, widget: QWidget, title: str, closeable: bool = True) -> int:
        # add tab to tabbar
        tab_index = self._tabbar.addTab(title)
        if not closeable:
            self._tabbar.setTabButton(tab_index, QTabBar.RightSide, None)
            self._tabbar.setTabButton(tab_index, QTabBar.LeftSide, None)  # it MAY be on the left too!!
        # add widget into stackedwidget
        self._stack.addWidget(widget)
        return tab_index

    def removeTab(self, index: int):
        # remove from tab bar
        self._tabbar.removeTab(index)
        # remove from stacked widget
        widget = self._stack.widget(index)
        if widget is not None:
            # Removes widget from the QStackedWidget. i.e., widget
            # is not deleted but simply removed from the stacked layout,
            # causing it to be hidden.
            self._stack.removeWidget(widget)
            # and now we probably want to delete it to avoid memory leak
            widget.close()
            widget.deleteLater()

    def tabBar(self) -> QTabBar:
        return self._tabbar

    def enableButtonAdd(self, enableState: bool = True):
        self._btn_add.setEnabled(enableState)

    def setCurrentIndex(self, index: int):
        self._stack.setCurrentIndex(index)
        self._tabbar.setCurrentIndex(index)

    def count(self) -> int:
        return self._tabbar.count()

    def tabWidget(self, index: int):
        """
        Return page widget, inserted at index index
        :param index:
        :return: QWidget inserted at specified index, or None
        """
        widget = self._stack.widget(index)
        return widget

    @pyqtSlot()
    def on_btn_add_clicked(self):
        self.addClicked.emit()

    @pyqtSlot(int)
    def on_tab_current_changed(self, idx: int):
        self._stack.setCurrentIndex(idx)
        self.currentChanged.emit(idx)

    @pyqtSlot(int)
    def on_tab_close_requested(self, idx: int):
        self.tabCloseRequested.emit(idx)
