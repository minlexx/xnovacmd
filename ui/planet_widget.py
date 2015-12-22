from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QVariant, QTimer
from PyQt5.QtWidgets import QWidget, QFrame, QMenu, QAction, \
    QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIcon, QCursor, QPixmap, QFont

from ui.xnova.xn_data import XNPlanet, XNCoords, XNPlanetBuildingItem
from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger

from ui.customwidgets.collapsible_frame import CollapsibleFrame

from ui.widget_utils import number_format

logger = xn_logger.get(__name__, debug=True)


class Planet_BasicInfoPanel(QFrame):

    requestOpenGalaxy = pyqtSignal(XNCoords)
    requestRefreshPlanet = pyqtSignal()

    def __init__(self, parent: QWidget):
        super(Planet_BasicInfoPanel, self).__init__(parent)
        #
        self._planet_pic_url = ''
        self._pixmap = QPixmap()
        self._planet = XNPlanet()
        # setup frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # bold font
        font = self.font()
        font.setWeight(QFont.Bold)
        # layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)
        self._vlayout = QVBoxLayout()
        self._hlayout_name_coords = QHBoxLayout()
        self._hlayout_fields = QHBoxLayout()
        self._hlayout_btn = QHBoxLayout()
        self._hlayout_res = QHBoxLayout()
        # labels
        self._lbl_img = QLabel(self)
        self._lbl_name = QLabel(self)
        self._lbl_coords = QLabel(self)
        self._lbl_coords.linkActivated.connect(self.on_coords_link_activated)
        self._lbl_fields = QLabel()
        # resource labels
        self._lbl_metal = QLabel(self.tr('Metal:'), self)
        self._lbl_crystal = QLabel(self.tr('Crystal:'), self)
        self._lbl_deit = QLabel(self.tr('Deiterium:'), self)
        self._lbl_cur_met = QLabel(self)
        self._lbl_cur_cry = QLabel(self)
        self._lbl_cur_deit = QLabel(self)
        self._lbl_cur_met.setFont(font)
        self._lbl_cur_cry.setFont(font)
        self._lbl_cur_deit.setFont(font)
        # button
        self._btn_refresh = QPushButton(self.tr('Refresh planet'), self)
        self._btn_refresh.setIcon(QIcon(':/i/reload.png'))
        self._btn_refresh.clicked.connect(self.on_btn_refresh_clicked)
        # finalize layout
        self._hlayout_name_coords.addWidget(self._lbl_name)
        self._hlayout_name_coords.addWidget(self._lbl_coords)
        self._hlayout_name_coords.addStretch()
        self._hlayout_fields.addWidget(self._lbl_fields)
        self._hlayout_fields.addStretch()
        self._hlayout_res.addWidget(self._lbl_metal)
        self._hlayout_res.addWidget(self._lbl_cur_met)
        self._hlayout_res.addWidget(self._lbl_crystal)
        self._hlayout_res.addWidget(self._lbl_cur_cry)
        self._hlayout_res.addWidget(self._lbl_deit)
        self._hlayout_res.addWidget(self._lbl_cur_deit)
        self._hlayout_res.addStretch()
        self._hlayout_btn.addWidget(self._btn_refresh)
        self._hlayout_btn.addStretch()
        self._vlayout.addLayout(self._hlayout_name_coords)
        self._vlayout.addLayout(self._hlayout_fields)
        self._vlayout.addLayout(self._hlayout_res)
        self._vlayout.addLayout(self._hlayout_btn)
        self._vlayout.addStretch()
        self._layout.addWidget(self._lbl_img)
        self._layout.addLayout(self._vlayout)
        self._layout.addStretch()
        #
        # setup timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.on_timer)

    def setup_from_planet(self, planet: XNPlanet):
        # store references
        self._planet = planet
        self._planet_pic_url = planet.pic_url
        # deal with planet pic
        file_name = './cache/img/{0}'.format(self._planet_pic_url.replace('/', '_'))
        self._pixmap = QPixmap(file_name)
        self._lbl_img.setPixmap(self._pixmap)
        # setup widget max height based on picture size and layout's margins
        margins = self._layout.contentsMargins()
        top_margin = margins.top()
        bottom_margin = margins.bottom()
        self.setMaximumHeight(self._pixmap.height() + top_margin + bottom_margin)
        # planet name, corods, fields
        self._lbl_name.setText(planet.name)
        self._lbl_coords.setText('<a href="{0}">{0}</a>'.format(planet.coords.coords_str()))
        self._lbl_fields.setText(self.tr('Fields:') +
                                 ' {0} / {1}'.format(planet.fields_busy, planet.fields_total))
        # resources
        self._set_resources()
        # restart timer
        self._timer.stop()
        self._timer.setInterval(1000)
        self._timer.setSingleShot(False)
        self._timer.start()

    def _set_resources(self):
        # update planet resources
        self._lbl_cur_met.setText(number_format(int(self._planet.res_current.met)))
        self._lbl_cur_cry.setText(number_format(int(self._planet.res_current.cry)))
        self._lbl_cur_deit.setText(number_format(int(self._planet.res_current.deit)))

    @pyqtSlot(str)
    def on_coords_link_activated(self, link: str):
        coords = XNCoords()
        coords.parse_str(link, raise_on_error=True)
        self.requestOpenGalaxy.emit(coords)

    @pyqtSlot()
    def on_btn_refresh_clicked(self):
        self.requestRefreshPlanet.emit()

    @pyqtSlot()
    def on_timer(self):
        self._set_resources()


class PlanetWidget(QFrame):
    """
    Provides view of galaxy/solarsystem contents as table widget
    """

    requestOpenGalaxy = pyqtSignal(XNCoords)

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
        self._layout.setSpacing(3)
        self.setLayout(self._layout)
        # basic info panel
        self._bipanel = Planet_BasicInfoPanel(self)
        self._bipanel.requestOpenGalaxy.connect(self.on_request_open_galaxy)
        self._bipanel.requestRefreshPlanet.connect(self.on_request_refresh_planet)
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
        self._layout.addStretch()

    def get_tab_type(self) -> str:
        return 'planet'

    def setPlanet(self, planet: XNPlanet):
        self._planet = planet
        self._bipanel.setup_from_planet(self._planet)

    def planet(self) -> XNPlanet:
        return self._planet

    @pyqtSlot(XNCoords)
    def on_request_open_galaxy(self, coords: XNCoords):
        self.requestOpenGalaxy.emit(coords)

    @pyqtSlot()
    def on_request_refresh_planet(self):
        logger.debug('Received request to reload planet {0}'.format(self._planet))
