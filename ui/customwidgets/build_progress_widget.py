from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, \
    QProgressBar, QPushButton
from PyQt5.QtGui import QFont, QIcon

from ui.xnova.xn_data import XNPlanet, XNPlanetBuildingItem
from ui.xnova import xn_logger


logger = xn_logger.get(__name__, debug=True)


class BuildProgressWidget(QFrame):

    BPW_TYPE_SHIPYARD = 'shipyard'
    BPW_TYPE_RESEARCH = 'research'

    requestCancelBuild = pyqtSignal(XNPlanetBuildingItem)
    requestCancelBuildWithPlanet = pyqtSignal(XNPlanetBuildingItem, int)

    def __init__(self, parent=None):
        super(BuildProgressWidget, self).__init__(parent)
        self._planet = XNPlanet()
        self._bitem = XNPlanetBuildingItem()
        # create UI
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(1)
        self.setLayout(self._layout)
        # label - planet name (0)
        self._lbl_planetName = QLabel(self)
        self._lbl_planetName.setText('')
        font = self._lbl_planetName.font()
        font.setWeight(QFont.Bold)  # fix label font weight to bold
        self._lbl_planetName.setFont(font)
        self._lbl_planetName.setMinimumWidth(120)
        self._layout.addWidget(self._lbl_planetName)
        # label - planet coords (1)
        self._lbl_planetCoords = QLabel(self)
        self._lbl_planetCoords.setText(' [0:0:0] ')
        self._lbl_planetCoords.setMinimumWidth(70)
        self._layout.addWidget(self._lbl_planetCoords)
        # label - building name (and lvl) (2)
        self._lbl_buildName = QLabel(self)
        self._lbl_buildName.setText('')
        self._lbl_buildName.setMinimumWidth(220)
        self._layout.addWidget(self._lbl_buildName)
        # label - build time left (3)
        self._lbl_buildTime = QLabel(self)
        self._lbl_buildTime.setText('')
        self._lbl_buildTime.setMinimumWidth(70)
        self._layout.addWidget(self._lbl_buildTime)
        # progress bar (4)
        self._pb = QProgressBar(self)
        self._pb.setRange(0, 99)
        self._pb.setValue(0)
        self._layout.addWidget(self._pb)
        # button cancel (5)
        self._btn_cancel = QPushButton(self)
        self._btn_cancel.setText('')
        self._btn_cancel.setIcon(QIcon(':i/cancel.png'))
        self._layout.addWidget(self._btn_cancel)
        self._btn_cancel.clicked.connect(self.on_btn_cancel)

    def __str__(self) -> str:
        ret = ''
        if self._planet is not None:
            ret += self._planet.name + ' '
        if self._bitem is not None:
            ret += self._bitem.name
            if self._bitem.is_shipyard_item:
                ret += ' (shipyard)'
            if self._bitem.is_research_item or \
                        self._bitem.is_researchfleet_item:
                ret += ' (research)'
        return ret

    def hide(self):
        super(BuildProgressWidget, self).hide()
        self._planet = None
        self._bitem = None

    def hide_planet_name(self):
        self._lbl_planetName.hide()
        self._lbl_planetCoords.hide()

    def _set_percent_complete(self, bi: XNPlanetBuildingItem):
        secs_passed = bi.seconds_total - bi.seconds_left
        percent_complete = (100 * secs_passed) // bi.seconds_total
        self._pb.setValue(percent_complete)

    def _set_buildtime(self, bi: XNPlanetBuildingItem):
        # calc and set time left
        secs_left = bi.seconds_left
        hours_left = secs_left // 3600
        secs_left -= hours_left * 3600
        mins_left = secs_left // 60
        secs_left -= mins_left * 60
        bl_str = '({0:02}:{1:02}:{2:02})'.format(
                hours_left, mins_left, secs_left)
        self._lbl_buildTime.setText(bl_str)

    def update_from_planet(self, planet: XNPlanet, typ: str = ''):
        self._planet = planet
        self._bitem = None
        # config UI
        self._lbl_planetName.setText(planet.name)
        self._lbl_planetCoords.setText(' [{0}:{1}:{2}] '.format(
                planet.coords.galaxy,
                planet.coords.system,
                planet.coords.position))
        if typ == '':
            # set from normal building
            if len(planet.buildings_items) > 0:
                for bi in planet.buildings_items:
                    if bi.is_in_progress():
                        self._bitem = bi
                        if not bi.is_downgrade:
                            bn = '{} {}->{}'.format(bi.name,
                                    bi.level, bi.level+1)
                        else:
                            bn = '[{}] {} {}->{}'.format(
                                    self.tr('Dismantle'), bi.name,
                                    bi.level, bi.level-1)
                        self._lbl_buildName.setText(bn)
                        self._set_percent_complete(bi)
                        self._set_buildtime(bi)
                        self.show()
                        return
            # if we are here, no builds are in progress
            self.hide()
            return
        elif typ == self.BPW_TYPE_SHIPYARD:
            self._btn_cancel.setEnabled(False)  # cannot cancel shipyard jobs
            # set from shipyard item
            for bi in planet.shipyard_progress_items:
                self._bitem = bi
                self._lbl_buildName.setText('{0} x {1} '.format(
                        bi.quantity, bi.name))
                self._set_percent_complete(bi)
                self._set_buildtime(bi)
                self.show()
                return
            # if we are here, no shipyard builds are in progress
            self.hide()
        elif typ == self.BPW_TYPE_RESEARCH:
            for bi in planet.research_items:
                if bi.is_in_progress():
                    self._bitem = bi
                    self._lbl_buildName.setText('{0} {1} '.format(
                            bi.name, bi.level+1))
                    self._set_percent_complete(bi)
                    self._set_buildtime(bi)
                    self.show()
                    return
            # also check researchfleet_items
            for bi in planet.researchfleet_items:
                if bi.is_in_progress():
                    self._bitem = bi
                    self._lbl_buildName.setText('{0} {1} '.format(
                            bi.name, bi.level+1))
                    self._set_percent_complete(bi)
                    self._set_buildtime(bi)
                    self.show()
                    return
            # if we are here, no researches in progress were found
            # (return is in previuos line)
            self.hide()
        else:
            logger.error('update_from_planet(): unknown type: {0}'.format(
                    typ))

    @pyqtSlot()
    def on_btn_cancel(self):
        if self._bitem is not None:
            if (self._bitem.remove_link is not None) and \
                        (self._bitem.remove_link != ''):
                self.requestCancelBuild.emit(self._bitem)
                self.requestCancelBuildWithPlanet.emit(
                        self._bitem, self._planet.planet_id)
