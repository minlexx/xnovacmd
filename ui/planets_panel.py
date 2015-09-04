from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFrame, QMessageBox
from PyQt5.QtGui import QPaintEvent, QPainter, QPainterPath, QFont, QFontMetrics, \
    QImage, QColor, QPen, QBrush

from .xnova.xn_data import XNPlanet
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class PlanetWidget(QFrame):
    def __init__(self, parent=None):
        super(PlanetWidget, self).__init__(parent)
        self._planet = XNPlanet()
        self._img = QImage()
        self._img_loaded = False
        self.init_ui()

    def init_ui(self):
        # logger.debug('PlanetWidget init UI')
        self.setMinimumSize(100, 100)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.StyledPanel)

    def _load_img(self):
        if self._planet.pic_url != '':
            file_name = './cache/img/{0}'.format(self._planet.pic_url.replace('/', '_'))
            logger.debug('Loading pic [{0}]'.format(file_name))
            if self._img.load(file_name):
                self._img_loaded = True
                return True
            self._img_loaded = False
            logger.warn('Could not load image: [{0}]'.format(file_name))

    def setPlanet(self, p: XNPlanet):
        self._planet = p
        self._load_img()

    @staticmethod
    def _drawOutlinedText(painter: QPainter, x: int, y: int, text: str,
                         font: QFont, textColor: QColor, outlineColor: QColor, outlineWidth: int=1):
        # setup outline path
        text_path = QPainterPath()
        text_path.addText(x, y, font, text)
        # draw outline path
        outlineBrush = QBrush(outlineColor, Qt.SolidPattern)
        outlinePen = QPen(outlineBrush, outlineWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(outlinePen)
        painter.setBrush(outlineBrush)
        painter.drawPath(text_path)
        # draw text
        painter.setPen(textColor)
        painter.setFont(font)
        painter.drawText(x, y, text)

    @staticmethod
    def _drawTextShadow(painter: QPainter, x: int, y: int, text: str, font: QFont, text_color: QColor):
        # setup outline path
        text_path = QPainterPath()
        text_path.addText(x, y, font, text)
        # draw outline path 1
        outline_color = QColor(0, 0, 0, 64)
        outline_brush = QBrush(outline_color, Qt.SolidPattern)
        outline_pen = QPen(outline_brush, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(outline_pen)
        painter.setBrush(outline_brush)
        painter.drawPath(text_path)
        # draw outline path 2
        outline_color = QColor(0, 0, 0, 128)
        outline_brush = QBrush(outline_color, Qt.SolidPattern)
        outline_pen = QPen(outline_brush, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(outline_pen)
        painter.setBrush(outline_brush)
        painter.drawPath(text_path)
        # draw text
        painter.setPen(text_color)
        painter.setFont(font)
        painter.drawText(x, y, text)

    def _drawPlanetPic(self, painter):
        if self._img_loaded:
            painter.drawImage(self.rect(), self._img, self._img.rect(), Qt.AutoColor)

    def _drawPlanetTitle(self, painter):
        font = QFont('Tahoma', 12)
        fontMetrics = QFontMetrics(font)
        font_h = fontMetrics.height()
        logger.debug('font h = {0}'.format(font_h))
        font.setStyleStrategy(QFont.ForceOutline)
        text_color = QColor(255, 255, 255, 255)  # rgba
        self._drawTextShadow(painter, 5, font_h, self._planet.name, font, text_color)

    def paintEvent(self, e: QPaintEvent):
        super(PlanetWidget, self).paintEvent(e)
        painter = QPainter(self)
        self._drawPlanetPic(painter)
        self._drawPlanetTitle(painter)
