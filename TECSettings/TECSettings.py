
from ..TECViewer_dialog import TECReadSettingDiag as settingsDiag
from qgis.core import QgsStyleV2, QgsVectorColorRampV2
from qgis.core import QgsVectorGradientColorRampV2
from PyQt4.QtGui import QListWidgetItem, QLinearGradient, QBrush, QPainter
from PyQt4.QtGui import QIcon, QPixmap, QGradient, QColor
from PyQt4.QtCore import QSize, QRect, QSettings
from PyQt4.QtSvg import QSvgGenerator
import os
import subprocess


class TECSettings:
    def __init__(self, iface, attributeList=list()):
        self.iface = iface
        self.dlg = settingsDiag()
        self.dlg.TECAttrList.clear()
        self.iconList = list()
        self.svgNameList = list()
        self.attributes = attributeList
        if self.attributes:
            self.setAttributeList()
        self.dlg.colorRampSelector.currentIndexChanged.connect(
            self.changeColorRamp)
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def setAttributeList(self):
        greyRamp = QgsStyleV2().defaultStyle().colorRamp('Greys').clone()
        for attr in self.attributes:
            if type(attr) == str:
                item = attrItem(self.dlg.TECAttrList, attr, greyRamp)
                self.dlg.TECAttrList.addItem(item)
                self.svgNameList.append(item.svgName)
                if item.svgName not in self.iconList:
                    self.iconList.append(item.svgName)
            elif type(attr) == list:
                item = attrItem(self.dlg.TECAttrList, attr[0], attr[1])
                self.dlg.TECAttrList.addItem(item)
                if item.svgName not in self.iconList:
                    self.iconList.append(item.svgName)

    def sendback(self):
        self.attributes = list()
        for i in range(0, self.dlg.TECAttrList.count()):
            item = self.dlg.TECAttrList.item(i)
            self.attributes.append([item.text(), item.currentRamp.clone()])

    def changeColorRamp(self, idx):
        currentItem = self.dlg.TECAttrList.currentItem()
        if not idx == 0:
            selectedRamp = self.dlg.colorRampSelector.currentColorRamp()
            currentItem.setColorRamp(selectedRamp.clone())
        else:
            greyRamp = QgsStyleV2().defaultStyle().colorRamp('Greys').clone()
            currentItem.setColorRamp(greyRamp)

    def writeSettings(self):
        if self.dlg.resolutionInput.text():
            try:
                res = float(self.dlg.resolutionInput.text())
                self.settings.setValue('resolution', res)
            except(AttributeError):
                pass
        if self.dlg.minDisInput.text():
            try:
                minDist = float(self.dlg.minDisInput.text())
                self.settings.setValue('min_Dist', minDist)
            except(AttributeError):
                pass

    def removeIcons(self):
        for _file in self.iconList:
            subprocess.Popen(['DEL', '/F', _file], shell=True)

    def run(self):
        result = self.dlg.exec_()
        if result == 1:
            self.writeSettings()
            self.sendback()
            self.removeIcons()
            return self.attributes


class attrItem(QListWidgetItem):
    def __init__(self, parent, attrName, defaultRamp):
        super(attrItem, self).__init__(parent)
        self.currentRamp = defaultRamp
        self.setText(attrName)
        self.setColorRamp(defaultRamp)

    def setColorRamp(self, ramp):
        self.currentRamp = ramp
        icon = self.drawIcon(ramp)
        self.setIcon(icon)

    def drawIcon(self, colorRamp):
        # input color ramp object: QgsVectorColorRampV2 object.
        # QgsVectorColorRampV2 is a virtual object, the real object name in
        # this case is QgsVectorGradientColorRampV2 object.
        mStops = colorRamp.stops()
        linearGradient = QLinearGradient(0.0, 50.0, 200.0, 50.0)
        for item in mStops:
            linearGradient.setColorAt(item.offset, item.color)
        linearGradient.setSpread(QGradient.PadSpread)

        svgName = os.path.join(os.path.dirname(__file__), self.text() + '.svg')
        pix = QSvgGenerator()
        pix.setFileName(svgName)
        pix.setSize(QSize(200, 100))
        painter = QPainter()
        painter.begin(pix)
        br = QBrush(linearGradient)
        painter.setBrush(br)
        painter.drawRect(QRect(0, 0, 200, 100))
        painter.end()

        pixmap = QPixmap(svgName)
        icon = QIcon(pixmap)
        self.svgName = svgName

        return icon
