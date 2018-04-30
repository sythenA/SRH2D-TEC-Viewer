
import os
from qgis.PyQt import QtGui, uic
from qgis.gui import QgsColorWheel, QgsPenStyleComboBox
from qgis.PyQt.QtGui import QSizePolicy
from qgis.PyQt.QtCore import Qt


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lineStyle.ui'))


class lineStyleChangeDiag(QtGui.QDialog, FORM_CLASS):
    AssignedColor = Qt.white

    def __init__(self, parent=None):
        super(lineStyleChangeDiag, self).__init__(parent)
        self.setupUi(self)

        self.QcolorWheel = QgsColorWheel(self.colorFrame)
        self.lineStyleCombo = QgsPenStyleComboBox(self.lineStyleFrame)
        self.widthAdjuster.setValue(3)


class lineStyleSelector:
    AssignedColor = Qt.black
    AssignedLineStyle = Qt.SolidLine

    def __init__(self, iface, init_Color=None, init_LineStyle=None,
                 init_Width=3):
        self.iface = iface
        self.dlg = lineStyleChangeDiag()

        self.dlg.QcolorWheel.colorChanged.connect(self.setColor)
        self.dlg.lineStyleCombo.currentIndexChanged.connect(self.setLineStyle)

        if init_Color:
            self.dlg.QcolorWheel.setColor(init_Color)
            self.AssignedColor = init_Color
        if init_LineStyle:
            self.dlg.lineStyleCombo.setPenStyle(init_LineStyle)
            self.AssignedLineStyle = init_LineStyle
        self.dlg.widthAdjuster.setValue(init_Width)

    def setColor(self, color):
        self.AssignedColor = color

    def setLineStyle(self):
        self.AssignedLineStyle = self.dlg.lineStyleCombo.penStyle()

    def run(self):
        result = self.dlg.exec_()

        if result == 1:
            widthVal = self.dlg.widthAdjuster.value()
            return self.AssignedColor, self.AssignedLineStyle, widthVal
