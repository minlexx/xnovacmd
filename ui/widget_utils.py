from PyQt5.QtCore import Qt, QCoreApplication
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


def flight_mission_for_humans(mis: str):
    if mis is None:
        return None
    if mis == 'owndeploy':
        return QCoreApplication.translate('FlightMission', 'Deploy')
    if mis == 'owntransport':
        return QCoreApplication.translate('FlightMission', 'Transport')
    if (mis == 'ownattack') or (mis == 'attack'):
        return QCoreApplication.translate('FlightMission', 'Attack')
    if (mis == 'ownespionage') or (mis == 'espionage'):
        return QCoreApplication.translate('FlightMission', 'Espionage')
    if mis == 'ownharvest':
        return QCoreApplication.translate('FlightMission', 'Harvest')
    if mis == 'owncolony':
        return QCoreApplication.translate('FlightMission', 'Colonize')
    if (mis == 'ownfederation') or (mis == 'federation'):
        return QCoreApplication.translate('FlightMission', 'Federation')
    if (mis == 'ownmissile') or (mis == 'missile'):
        return QCoreApplication.translate('FlightMission', 'I-P Missile')
    if mis == 'ownbase':
        return QCoreApplication.translate('FlightMission', 'Create base')
    if (mis == 'owndestroy') or (mis == 'destroy'):
        return QCoreApplication.translate('FlightMission', 'Destroy')
    if mis == 'ownhold':
        return QCoreApplication.translate('FlightMission', 'Hold')
    return QCoreApplication.translate('FlightMission', 'Mission unknown')


def number_format(num: int) -> str:
    if num == 0:
        return '0'
    s = ''
    r = abs(num)
    while r > 0:
        ost = r % 1000
        r = (r // 1000)
        # pad with zeroes each triplet
        s = '{0:03}'.format(ost) + s
        if r > 0:
            s = '.' + s
    # remove leading zeroes
    if s.startswith('00'):
        s = s[2:]
    elif s.startswith('0'):
        s = s[1:]
    # add sign, if needed
    if num < 0:
        s = '-' + s
    return s
