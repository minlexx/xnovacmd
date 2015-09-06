from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QPoint, QRect
from PyQt5.QtWidgets import QWidget, QFrame, QMessageBox
from PyQt5.QtGui import QPaintEvent, QPainter, QPainterPath, QFont, QFontMetrics, \
    QImage, QColor, QPen, QBrush, QMouseEvent

from .xnova.xn_data import XNCoords, XNPlanet
from .xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class PWToolTipInfo:
    def __init__(self, parent=None):
        self._visible = False
        self._x = 0
        self._y = 0
        self._text = ''
        self._bgcolor = QColor(0, 0, 0, 128)
        self._frame_color = QColor(0, 0, 0, 0)
        self._text_color = QColor(255, 255, 255)
        self._font = QFont('Tahoma', 8)
        self._fm = QFontMetrics(self._font)
        self._margin = 5

    def set_font(self, font: QFont):
        self._font = font
        self._fm = QFontMetrics(self._font)

    def show_tt(self, x, y, text: str):
        self._visible = True
        self._x = x
        self._y = y
        self._text = text

    def hide(self):
        self._visible = False

    def isVisible(self):
        return self._visible

    def draw(self, painter: QPainter):
        if not self._visible:
            return
        bg_brush = QBrush(self._bgcolor, Qt.SolidPattern)
        b_rect = self._fm.boundingRect(self._text)
        b_rect.adjust(0, 0, self._margin, self._margin)
        b_rect.moveTo(self._x, self._y)
        painter.setPen(self._frame_color)
        painter.setBrush(bg_brush)
        painter.drawRect(b_rect)
        painter.setPen(self._text_color)
        painter.setFont(self._font)
        painter.drawText(b_rect, Qt.AlignCenter, self._text)


class PlanetWidget(QFrame):
    requestOpenPlanet = pyqtSignal(int)
    requestOpenGalaxy = pyqtSignal(XNCoords)

    def __init__(self, parent=None):
        super(PlanetWidget, self).__init__(parent)
        self._planet = XNPlanet()
        self._img = QImage()
        self._img_loaded = False
        self._mouse_over_planet_name = False
        self._mouse_over_planet_coords = False
        self._mouse_over_planet_fields = False
        self._tt = PWToolTipInfo()
        self._pb_texture = QImage()
        self.init_ui()

    def init_ui(self):
        # logger.debug('PlanetWidget init UI')
        self.setMinimumSize(88, 88)
        self.setMaximumSize(88, 88)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMouseTracking(True)
        if not self._pb_texture.load(':/i/pb01_tex.png'):
            logger.warn('Failed to load progress bar texture!')

    def _load_img(self):
        if self._planet.pic_url != '':
            file_name = './cache/img/{0}'.format(self._planet.pic_url.replace('/', '_'))
            # logger.debug('Loading pic [{0}]'.format(file_name))
            if self._img.load(file_name):
                self._img_loaded = True
                return True
            self._img_loaded = False
            logger.warn('Could not load image: [{0}]'.format(file_name))

    @pyqtSlot(XNPlanet)
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

    def _drawPlanetPic(self, painter: QPainter):
        if self._img_loaded:
            painter.drawImage(self._img.rect(), self._img, self._img.rect(), Qt.AutoColor)

    def _drawPlanetTitle(self, painter: QPainter):
        font = QFont('Tahoma', 10, QFont.Bold)
        font_coords = QFont('Tahoma', 8)
        font_metrics = QFontMetrics(font)
        font_h = font_metrics.height()
        # logger.debug('font h = {0}'.format(font_h))
        font.setStyleStrategy(QFont.ForceOutline)
        text_color = QColor(255, 255, 255, 255)  # rgba
        self._drawTextShadow(painter, 5, 1+font_h, self._planet.name, font, text_color)
        # planet coords
        scoords = '[{0}:{1}:{2}]'.format(self._planet.coords.galaxy,
                            self._planet.coords.system,
                            self._planet.coords.position)
        self._drawTextShadow(painter, 5, 1+font_h+2+font_h, scoords, font_coords, text_color)

    def _drawFields(self, painter: QPainter):
        ratio = self._planet.fields_busy / self._planet.fields_total
        pb_width = int(self.width() * ratio)
        w = self._pb_texture.height()
        fb = QBrush(self._pb_texture)
        painter.setPen(Qt.NoPen)
        painter.setBrush(fb)
        r = QRect(0, self.height()-w, pb_width, w)
        painter.drawRect(r)

    def _drawToolTip(self, painter: QPainter):
        self._tt.draw(painter)

    def paintEvent(self, e: QPaintEvent):
        super(PlanetWidget, self).paintEvent(e)
        painter = QPainter(self)
        self._drawPlanetPic(painter)
        self._drawPlanetTitle(painter)
        self._drawFields(painter)
        self._drawToolTip(painter)

    def mouseMoveEvent(self, event: QMouseEvent):
        super(PlanetWidget, self).mouseMoveEvent(event)
        # QMouseEvent::pos() reports the position of the mouse cursor, relative to this widget.
        mx = event.x()
        my = event.y()
        # global_mouse_pos = event.globalPos()
        fields_pb_h = self._pb_texture.height()
        # remember prev
        prev_mouse_over_planet_name = self._mouse_over_planet_name
        prev_mouse_over_planet_coords = self._mouse_over_planet_coords
        self._mouse_over_planet_name = False
        self._mouse_over_planet_coords = False
        self._mouse_over_planet_fields = False
        # calculate
        if (my >= 3) and (my <= 23):
            self._mouse_over_planet_name = True
        if (my >= 24) and (my <= 35):
            self._mouse_over_planet_coords = True
        if (my >= self.height()-fields_pb_h) and (my <= self.height()):
            self._mouse_over_planet_fields = True
        # detect change
        change = False
        if prev_mouse_over_planet_name != self._mouse_over_planet_name:
            change = True
        if prev_mouse_over_planet_coords != self._mouse_over_planet_coords:
            change = True
        self._tt.hide()
        if change:
            if self._mouse_over_planet_name or self._mouse_over_planet_coords:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        if self._mouse_over_planet_name:
            self._tt.show_tt(0, 40, self.tr('Go to planet'))
        if self._mouse_over_planet_coords:
            self._tt.show_tt(0, 40, self.tr('Go to galaxy'))
        if self._mouse_over_planet_fields:
            self._tt.show_tt(0, 40, self.tr('Field: {0}/{1}').format(
                self._planet.fields_busy, self._planet.fields_total))
        self.update()

    # def enterEvent(self, event):
    #    super(PlanetWidget, self).enterEvent(event)

    def leaveEvent(self, event):
        super(PlanetWidget, self).leaveEvent(event)
        self._tt.hide()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        button = event.button()
        if button == Qt.LeftButton:
            if self._mouse_over_planet_name:
                # logger.debug('planet name click')
                self.requestOpenPlanet.emit(self._planet.planet_id)
            elif self._mouse_over_planet_coords:
                # logger.debug('planet coords click')
                self.requestOpenGalaxy.emit(self._planet.coords)

