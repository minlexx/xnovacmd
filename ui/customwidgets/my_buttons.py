from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QPoint, QSize, QRect
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtGui import QIcon, QImage, QPixmap, QPaintEvent, QPainter, QPainterPath, QFont, QFontMetrics, \
    QColor, QPen, QBrush

from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class ButtonTextOverIcon(QPushButton):
    """
    Button that displays outlined text over icon, not by side
    """
    def __init__(self, parent=None):
        super(ButtonTextOverIcon, self).__init__(parent)
        # set default values
        self.setOutlineColorWidth(QColor(255, 255, 255, 64), 3)
        self.setTextColor(QColor(64, 64, 64))
        # fix font bold
        font = self.font()
        font.setWeight(QFont.Bold)
        self.setFont(font)

    def setTextColor(self, color: QColor):
        self.text_color = color

    def setOutlineColorWidth(self, color: QColor, width: int):
        self.outline_color = color
        self.outline_brush = QBrush(self.outline_color, Qt.SolidPattern)
        self.outline_pen = QPen(self.outline_brush, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    def _drawTextShadow(self, painter: QPainter, x: int, y: int, text: str):
        font = self.font()
        # setup outline path
        text_path = QPainterPath()
        text_path.addText(x, y, font, text)
        # draw outline path 1
        painter.setPen(self.outline_pen)
        painter.setBrush(self.outline_brush)
        painter.drawPath(text_path)
        # draw text
        painter.setPen(self.text_color)
        painter.setFont(font)
        # Note: The y-position is used as the baseline of the font.
        painter.drawText(x, y, text)

    def paintEvent(self, evt: QPaintEvent):
        # save our text
        text = self.text()
        self.setText('')
        # default painting, should paint icon
        super(ButtonTextOverIcon, self).paintEvent(evt)
        # calculate the width of text in pixels
        font = self.font()
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.width(text)
        text_height = font_metrics.height()
        # calculate text output coordinates centered
        w = self.width()
        h = self.height()
        x = w//2 - text_width//2
        y = h//2 - text_height//2
        # draw text, centered inside window
        painter = QPainter(self)
        y += font_metrics.ascent()  # Note: The y-position is used as the baseline of the font. add it
        self._drawTextShadow(painter, x, y, text)
        # restore text
        self.setText(text)
