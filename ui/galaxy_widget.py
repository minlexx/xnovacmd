from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QMenu, QAction, \
    QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIcon, QCursor

from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger


logger = xn_logger.get(__name__, debug=True)


class GalaxyView(QFrame):
    """
    Provides view of galaxy/solarsystem contents as table widget
    """
    def __init__(self, parent: QWidget):
        super(GalaxyView, self).__init__(parent)
        self.world = XNovaWorld_instance()
        #
        # setup frame
        self.setFrameShadow(QFrame.Raised)
        self.setFrameShape(QFrame.StyledPanel)
        #
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        # temp
        self._layout.addWidget(QLabel('galaxy view', self))


class GalaxyCoordSingleSelectorWidget(QFrame):
    """
    Provides single control to select coordinate
    Displays button to navigate left, right
    and text edit field to input coordinate manually
    Displays coordinate name above, as title
    """

    coordChanged = pyqtSignal(int)

    def __init__(self, parent: QWidget):
        super(GalaxyCoordSingleSelectorWidget, self).__init__(parent)
        # data
        self._coord_value = 1
        self._coord_min = 1
        self._coord_max = 100
        self._title = 'Coord select'
        #
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        #
        self._layout = QVBoxLayout()
        self._layout_buttons = QHBoxLayout()
        self._lbl_title = QLabel(self)
        self._btn_left = QPushButton(self)
        self._btn_right = QPushButton(self)
        self._le_coord = QLineEdit(self)
        #
        self._lbl_title.setText(self._title)
        self._btn_left.setText('<-')
        self._btn_left.setMaximumWidth(32)
        self._btn_left.clicked.connect(self.on_left)
        self._btn_right.setText('->')
        self._btn_right.setMaximumWidth(32)
        self._btn_right.clicked.connect(self.on_right)
        self._le_coord.setText(str(self._coord_value))
        self._le_coord.setMaximumWidth(32)
        self._le_coord.returnPressed.connect(self.on_le_returnPressed)
        self._le_coord.editingFinished.connect(self.on_le_editFinished)
        #
        self._layout.addWidget(self._lbl_title, 0, Qt.AlignCenter)
        self._layout_buttons.addWidget(self._btn_left)
        self._layout_buttons.addWidget(self._le_coord)
        self._layout_buttons.addWidget(self._btn_right)
        self._layout.addLayout(self._layout_buttons)
        self.setLayout(self._layout)

    def coord(self) -> int:
        return self._coord_value

    def coordMin(self) -> int:
        return self._coord_min

    def coordMax(self) -> int:
        return self._coord_max

    def setCoord(self, coord_v: int):
        self._coord_value = coord_v
        if self._coord_value <= self._coord_min:
            self._coord_value = self._coord_min
        if self._coord_value >= self._coord_max:
            self._coord_value = self._coord_max
        self._le_coord.setText(str(self._coord_value))

    def setCoordRange(self, coord_min: int, coord_max: int):
        self._coord_min = coord_min
        self._coord_max = coord_max

    def title(self) -> str:
        return self._title

    def setTitle(self, title: str):
        self._title = title
        self._lbl_title.setText(self._title)

    @pyqtSlot()
    def on_left(self):
        prev_value = self._coord_value
        self._coord_value -= 1
        self.setCoord(self._coord_value)
        if self._coord_value != prev_value:
            self.coordChanged.emit(self._coord_value)

    @pyqtSlot()
    def on_right(self):
        prev_value = self._coord_value
        self._coord_value += 1
        self.setCoord(self._coord_value)
        if self._coord_value != prev_value:
            self.coordChanged.emit(self._coord_value)

    def _read_lineedit_value(self, do_emit: bool = True):
        prev_value = self._coord_value
        txt = self._le_coord.text()
        val = self._coord_value
        try:
            val = int(txt)
        except ValueError:
            pass
        self.setCoord(val)
        if do_emit:
            if self._coord_value != prev_value:
                self.coordChanged.emit(self._coord_value)

    @pyqtSlot()
    def on_le_returnPressed(self):
        # logger.debug('return pressed')
        self._read_lineedit_value(do_emit=True)

    @pyqtSlot()
    def on_le_editFinished(self):
        # logger.debug('edit finished')
        self._read_lineedit_value(do_emit=False)


class GalaxyCoordsSelectorWidget(QFrame):
    """
    Groups together two controls to select galaxy and system
    coordinates with a button to navigate there.
    TODO: it can also show selector of your current planets,
    TODO: and maybe bookmarks? :D
    """

    coordsChanged = pyqtSignal(int, int)

    def __init__(self, parent: QWidget):
        super(GalaxyCoordsSelectorWidget, self).__init__(parent)
        # data
        self._coords = [1, 1]  # galaxy, system
        #
        # setup frame
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)
        #
        self._layout = QHBoxLayout()
        self.setLayout(self._layout)
        #
        self._galaxy_selector = GalaxyCoordSingleSelectorWidget(self)
        self._galaxy_selector.setCoordRange(1, 5)
        self._galaxy_selector.setTitle(self.tr('Galaxy'))
        self._galaxy_selector.coordChanged.connect(self.on_gal_changed)
        self._system_selector = GalaxyCoordSingleSelectorWidget(self)
        self._system_selector.setCoordRange(1, 499)
        self._system_selector.setTitle(self.tr('Solar system'))
        self._system_selector.coordChanged.connect(self.on_sys_changed)
        #
        self._btn_navigate = QPushButton(self)
        self._btn_navigate.setText(self.tr('Navigate'))
        self._btn_navigate.clicked.connect(self.on_btn_navigate)
        #
        self._layout.addWidget(self._galaxy_selector)
        self._layout.addWidget(self._system_selector)
        self._layout.addWidget(self._btn_navigate)
        self._layout.addStretch()

    def coordGalaxy(self) -> int:
        return self._coords[0]

    def coordSystem(self) -> int:
        return self._coords[1]

    def coords(self) -> list:
        return self._coords

    def setCoords(self, galaxy: int, system: int):
        prev_coords = self._coords
        self._galaxy_selector.setCoord(galaxy)  # does all range-checking
        self._system_selector.setCoord(system)  # does all range-checking
        # get actual fixed coords
        self._coords[0] = self._galaxy_selector.coord()
        self._coords[1] = self._system_selector.coord()
        # compare and emit
        if (prev_coords[0] != self._coords[0]) or (prev_coords[1] != self._coords[1]):
            self.coordsChanged.emit(self._coords[0], self._coords[1])

    def setGalaxyRange(self, gal_min: int, gal_max: int):
        self._galaxy_selector.setCoordRange(gal_min, gal_max)

    def setSystemRange(self, sys_min: int, sys_max: int):
        self._system_selector.setCoordRange(sys_min, sys_max)

    @pyqtSlot(int)
    def on_gal_changed(self, c: int):
        self._coords[0] = c
        self.coordsChanged.emit(self._coords[0], self._coords[1])

    @pyqtSlot(int)
    def on_sys_changed(self, c: int):
        self._coords[1] = c
        self.coordsChanged.emit(self._coords[0], self._coords[1])

    @pyqtSlot()
    def on_btn_navigate(self):
        # get actual coords
        self._coords[0] = self._galaxy_selector.coord()
        self._coords[1] = self._system_selector.coord()
        # just force refresh like coords changed
        self.coordsChanged.emit(self._coords[0], self._coords[1])


class GalaxyWidget(QWidget):
    """
    Serves as container for galaxy coords selector widget
    and galaxy view widget. All this container can be added
    as a signle widget (tab page).
    """

    def __init__(self, parent: QWidget):
        super(GalaxyWidget, self).__init__(parent)
        self.world = XNovaWorld_instance()
        # main layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self.setLayout(self._layout)
        # sub-widgets
        self._galaxy_coords = GalaxyCoordsSelectorWidget(self)
        self._galaxy_coords.setGalaxyRange(1, 5)
        self._galaxy_coords.setSystemRange(1, 499)
        self._galaxy_coords.coordsChanged.connect(self.on_coords_cahnged)
        self._galaxyview = GalaxyView(self)
        # scrollarea
        self._sa_galaxy = QScrollArea(self)
        self._sa_galaxy.setMinimumWidth(400)
        self._sa_galaxy.setMinimumHeight(300)
        self._sa_galaxy.setWidget(self._galaxyview)
        #
        self._layout.addWidget(self._galaxy_coords)
        self._layout.addWidget(self._sa_galaxy)

    @pyqtSlot(int, int)
    def on_coords_cahnged(self, gal: int, sys: int):
        logger.debug('on_coords_changed ({0}, {1})'.format(gal, sys))
