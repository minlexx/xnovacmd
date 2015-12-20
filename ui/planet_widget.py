from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QMenu, QAction, \
    QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIcon, QCursor

from ui.xnova.xn_data import XNPlanet, XNCoords, XNPlanetBuildingItem
from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger

from ui.customwidgets.collapsible_frame import CollapsibleFrame

logger = xn_logger.get(__name__, debug=True)


class Planet_BasicInfoPanel(QFrame):
    def __init__(self, parent: QWidget):
        super(Planet_BasicInfoPanel, self).__init__(parent)
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self.setLayout(self._layout)

    def setup_from_planet(self, pl: XNPlanet):
        pass


class PlanetWidget(QFrame):
    """
    Provides view of galaxy/solarsystem contents as table widget
    """
    def __init__(self, parent: QWidget):
        super(PlanetWidget, self).__init__(parent)
        #
        self.world = XNovaWorld_instance()
        self._planet = XNPlanet()
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self.setLayout(self._layout)
        # basic info panel
        self._bipanel = Planet_BasicInfoPanel(self)
        # buildings
        self._cf_buildings = CollapsibleFrame(self)
        self._cf_buildings.setTitle(self.tr('Buildings'))
        # shipyard
        self._cf_shipyard = CollapsibleFrame(self)
        self._cf_shipyard.setTitle(self.tr('Shipyard'))
        # research
        self._cf_research = CollapsibleFrame(self)
        self._cf_research.setTitle(self.tr('Research'))
        # layout finalize
        self._layout.addWidget(self._bipanel)
        self._layout.addWidget(self._cf_buildings)
        self._layout.addWidget(self._cf_shipyard)
        self._layout.addWidget(self._cf_research)

    def get_tab_type(self):
        return 'planet'

    def setPlanet(self, planet: XNPlanet):
        self._planet = planet

    def planet(self) -> XNPlanet:
        return self._planet
