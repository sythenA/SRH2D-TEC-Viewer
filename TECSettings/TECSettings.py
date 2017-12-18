
from ..TECViewer_dialog import TECReadSettingDiag as settingsDiag
from ..TECViewer_dialog import Settings
from qgis.core import QgsStyleV2, QgsVectorColorRampV2
from qgis.core import QgsVectorGradientColorRampV2
from PyQt4.QtGui import QListWidgetItem, QLinearGradient, QBrush, QPainter
from PyQt4.QtGui import QIcon, QPixmap, QGradient, QColor
from PyQt4.QtCore import QSize, QRect
from PyQt4.QtSvg import QSvgGenerator
import os


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

    def setAttributeList(self):
        # greyRamp = QgsStyleV2().defaultStyle().colorRamp('Greys').properties()
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
        selectedRamp = self.dlg.colorRampSelector.currentColorRamp()
        currentItem.setColorRamp(selectedRamp.clone())

    def writeSettings(self):
        filePath = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                '_settings_')
        f = open(filePath, 'w')
        if self.dlg.resolutionInput.text():
            try:
                res = float(self.dlg.resolutionInput.text())
                Settings.update({'resolution': res})
            except:
                pass
        if self.dlg.minDisInput.text():
            try:
                minDist = float(self.dlg.minDisInput.text())
                Settings.update({'min_Dist': minDist})
            except:
                pass
        for key in Settings.keys():
            f.write(key + ' = ' + str(Settings[key]) + '\n')
        f.close()

    def removeIcons(self):
        for _file in self.iconList:
            os.system('DEL /F "' + _file + '"' + ' >/dev/null 2>&1')

    def run(self):
        result = self.dlg.exec_()
        if result == 1:
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
        FirstPColor = colorRamp.color(0.0)
        SecondPColor = colorRamp.color(0.25)
        ThirdPColor = colorRamp.color(0.5)
        FourthPColor = colorRamp.color(0.75)
        FifthPColor = colorRamp.color(1.0)
        linearGradient = QLinearGradient(0.0, 50.0, 200.0, 50.0)
        linearGradient.setColorAt(0.0, FirstPColor)
        linearGradient.setColorAt(0.25, SecondPColor)
        linearGradient.setColorAt(0.5, ThirdPColor)
        linearGradient.setColorAt(0.75, FourthPColor)
        linearGradient.setColorAt(1.0, FifthPColor)
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
