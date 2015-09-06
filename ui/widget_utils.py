from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLayout, QBoxLayout, QLayoutItem


def install_layout_for_widget(widget, orientation=None, margins=None, spacing=None):
    """
    Installs a layout to widget, if it does not have it already.
    :param widget: target widget
    :param orientation: Qt.Vertical (default) / Qt.Horizontal
    :param margins: layou margins = (11, 11, 11, 11) from Qt docs, style dependent
    :param spacing: spacing between items in layout
    :return: None
    """
    if widget.layout():
        return  # already has a layout
    direction = QBoxLayout.TopToBottom
    if orientation == Qt.Horizontal:
        direction = QBoxLayout.LeftToRight
    l = QBoxLayout(direction)
    if margins:
        l.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
    if spacing:
        l.setSpacing(spacing)
    widget.setLayout(l)


def remove_trailing_spacer_from_layout(layout: QLayout):
    """
    If the last item in the layout is spacer, removes it.
    :param layout: target layout
    :return: bool success indicator
    """
    ni = layout.count()
    if ni < 1:
        return False
    ni -= 1
    layout_item = layout.itemAt(ni)
    if layout_item is None:
        return False
    spacer_item = layout_item.spacerItem()
    if spacer_item is not None:
        layout.removeItem(spacer_item)
        return True
    return False


def append_trailing_spacer_to_layout(layout: QBoxLayout):
    layout.addStretch()

