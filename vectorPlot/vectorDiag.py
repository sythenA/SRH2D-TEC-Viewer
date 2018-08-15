
import os
from qgis.core import QgsMapLayerRegistry, QgsMarkerSymbolV2
from qgis.core import QgsSimpleMarkerSymbolLayerV2, QgsDataDefined, QgsSymbolV2
from qgis.core import QgsVectorFieldSymbolLayer, QgsSingleSymbolRendererV2
from qgis.core import QgsField
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtGui import QFileDialog, QListWidgetItem, QColor, QMenu
from qgis.PyQt.QtCore import QSettings, QVariant
from ..tools.TECfile import TECfile
from random import randint
import subprocess


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'vectorPlot.ui'))


class vecPlotDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(vecPlotDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        self.addTecBtn.clicked.connect(self.addTecFiles)
        self.deleteTecBtn.clicked.connect(self.deleteTecFile)

    def addTecFiles(self):
        simFolder = os.path.join(self.settings.value('projFolder'), 'sim')
        TecFiles = QFileDialog().getOpenFileNames(directory=simFolder)
        if TecFiles:
            for file in TecFiles:
                item = TECfile(self.tecList, QListWidgetItem.Type, file,
                               self.iface)
                item.readTEC(file)
                item.readVariables(item.dat)
                self.tecList.addItem(item)
                self.addAttribute()

    def deleteTecFile(self):
        self.tecList.takeItem(self.tecList.currentRow())

    def addAttribute(self):
        item = self.tecList.item(0)
        _attr = item.attributes
        attributes = list()
        for item in _attr:
            attributes.append(item[0])

        if self.xAttrCombo.count() == 0:
            self.xAttrCombo.addItems(attributes)
            self.yAttrCombo.addItems(attributes)


class vecPlot:
    def __init__(self, iface):
        self.iface = iface
        self.settings = QSettings('MantSplendid', 'SRH2D_TEC_Viewer')
        self.registry = QgsMapLayerRegistry.instance()

        self.dlg = vecPlotDialog(self.iface)
        self.dlg.tecList.customContextMenuRequested.connect(
            self.rightClickOnItem)

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()

        defaultFolder = self.defaultFolder()
        if result:
            self.xAttr = self.dlg.xAttrCombo.currentText()[0:10]
            self.yAttr = self.dlg.yAttrCombo.currentText()[0:10]

            self.setOutput(defaultFolder)

    def defaultFolder(self):
        projFolder = self.settings.value('projFolder')

        if projFolder:
            outDir = os.path.join(projFolder, 'FlowDirection')

            if os.path.isdir(self.outDir):
                subprocess.call(['cmd', '/c', 'RD', '/S', '/Q', outDir])
                subprocess.call(['cmd', '/c', 'mkdir', outDir])
            else:
                subprocess.call(['cmd', '/c', 'mkdir', outDir])

            return outDir
        else:
            return ''

    def rightClickOnItem(self, pos):
        cursorPos = self.dlg.tecList.mapToGlobal(pos)
        subMenu = QMenu()
        subMenu.addAction('Set Out Folder', self.setItemFolder)
        subMenu.addAction('Set XY Attribute', self.individualTECAttrSetting)

        subMenu.exec_(cursorPos)

    def individualTECAttrSetting(self):
        item = self.dlg.tecList.currentItem()
        settingDiag = attrSettingDiag(item.attributes)
        xAttr, yAttr = settingDiag.run()

        item.xAttr = xAttr
        item.yAttr = yAttr

    def addAttributeToLayer(self, layer, xAttr, yAttr):
        layer.startEditing()
        layer.addAttribute(QgsField("size", QVariant.Int, len=5))

        for feature in layer.getFeatures():
            VelMeg = feature[xAttr]**2 + feature[yAttr]**2
            idx = feature.fieldNameIndex('size')
            if VelMeg > 0:
                layer.changeAttributeValue(feature.id(), idx, 5)
                # feature.setAttribute(idx, 5)
            else:
                layer.changeAttributeValue(feature.id(), idx, 0)
                # feature.setAttribute(idx, 0)

        layer.commitChanges()

    def setOutput(self, presetFolder):
        outputFolder = QFileDialog().getExistingDirectory(
            directory=presetFolder)
        for i in range(0, self.dlg.tecList.count()):
            item = self.dlg.tecList.item(i)
            if not item.outDir:
                item.outDir = outputFolder
            item.genNodeLayer()
            vlayer = self.registry.addMapLayer(item.nodeLayer)
            if item.xAttr:
                xAttr = item.xAttr
            else:
                xAttr = self.xAttr
            if item.yAttr:
                yAttr = item.yAttr
            else:
                yAttr = self.yAttr

            self.addAttributeToLayer(item.nodeLayer, xAttr, yAttr)
            renderer = self.buildRenderer(xAttr, yAttr)
            vlayer.setRendererV2(renderer)

    def setItemFolder(self):
        item = self.dlg.tecList.currentItem()
        fileFolder = os.path.dirname(item.filePath)
        outputFolder = QFileDialog().getExistingDirectory(
            directory=fileFolder)
        if outputFolder:
            item.outDir = outputFolder

    def buildRenderer(self, xAttr, yAttr):
        color = QColor(randint(0, 255), randint(0, 255), randint(0, 255))
        symbol = QgsMarkerSymbolV2.createSimple({})
        symbol.deleteSymbolLayer(0)

        prop = QgsDataDefined()
        prop.setField("size")
        prop.setActive(True)

        symbol_layer = QgsSimpleMarkerSymbolLayerV2()
        symbol_layer.setColor(color)
        symbol_layer.setOutputUnit(QgsSymbolV2.MapUnit)
        symbol_layer.setDataDefinedProperty("size", prop)
        symbol.appendSymbolLayer(symbol_layer)

        symbol_layer = QgsVectorFieldSymbolLayer()
        symbol_layer.setColor(color)
        symbol_layer.VectorFieldType(QgsVectorFieldSymbolLayer.Cartesian)
        symbol_layer.AngleUnits(QgsVectorFieldSymbolLayer.Degrees)
        symbol_layer.setXAttribute(xAttr)
        symbol_layer.setYAttribute(yAttr)
        symbol.appendSymbolLayer(symbol_layer)

        renderer = QgsSingleSymbolRendererV2(symbol)

        return renderer


FORM_CLASS2, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attrSettings.ui'))


class attrSettingDiag(QtGui.QDialog, FORM_CLASS2):
    def __init__(self, attributes, parent=None):
        super(attrSettingDiag, self).__init__(parent)
        self.setupUi(self)

        self.setAttribute(attributes)

    def setAttribute(self, _attributes):
        attributesList = list()
        for attr in _attributes:
            attributesList.append(attr[0])

        self.xAttrCombo.addItems(attributesList)
        self.yAttrCombo.addItems(attributesList)

    def run(self):
        self.show()
        result = self.exec_()
        if result:
            return self.xAttrCombo.currentText()[0:10], self.yAttrCombo.currentText()[0:10]


"""
class itemAttrSetting:
    def __init__(self, attributes):
        self.dlg = attrSettingDiag(attributes)

    def run(self):"""
