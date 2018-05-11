
from contourPlotDiag import contourGenDialog
from qgis.core import QgsProject, QgsMapLayerRegistry, QgsRasterLayer
from qgis.PyQt.QtGui import QTreeWidgetItem, QFileDialog
from qgis.PyQt.QtCore import Qt
from osgeo import gdal
import os
from ..tools.TECBoxItem import layerItem


def changeCheckState(item):
    if item.checkState(0) == Qt.Unchecked:
        item.setCheckState(0, Qt.Checked)
    else:
        item.setCheckState(0, Qt.Unchecked)
    return item


def removeChildItem(treeWidget, cItem):
    for i in range(0, treeWidget.topLevelItemCount()):
        if treeWidget.topLevelItem[i].indexOfChild(cItem):
            treeWidget.topLevelItem[i].takeChild(cItem)


class contourPlot:
    def __init__(self, iface):
        self.iface = iface
        self.dlg = contourGenDialog()

        registry = QgsMapLayerRegistry.instance()
        registry.legendLayersAdded.connect(self.layerFromRegistry)
        registry.layerRemoved.connect(self.layerFromRegistry)

        self.dlg.attrSelectBtn.clicked.connect(self.attrSelected)
        self.dlg.layersAddBtn.clicked.connect(self.addToGenContour)
        self.dlg.layersDeleteBtn.clicked.connect(self.removeFromAdded)
        self.dlg.removeAllBtn.clicked.connect(self.cleanSelected)

    def layerFromRegistry(self):
        all_attrs = list()
        self.dlg.currentLayers.clear()
        root = QgsProject.instance().layerTreeRoot()
        for node in root.children():
            if len(node.children()) > 0:
                pWidget = QTreeWidgetItem(self.dlg.currentLayers, node.name())
                pWidget.setText(0, node.name())
                for layer in node.children():
                    if type(layer.layer()) == QgsRasterLayer:
                        attrName = layer.name()
                        attrLayerId = layer.layerId()

                        all_attrs.append(attrName)

                        cWidget = layerItem(pWidget, attrName, attrLayerId)
                        cWidget.setCheckState(0, Qt.Unchecked)
                        pWidget.addChild(cWidget)
                self.dlg.currentLayers.addTopLevelItem(pWidget)
            else:
                attrName = node.name()
                all_attrs.append(attrName)
                attrLayerId = node.layerId()
                pWidget = layerItem(self.dlg.currentLayers, attrName,
                                    attrLayerId)
                pWidget.setCheckState(0, Qt.Unchecked)
                self.dlg.currentLayers.addTopLevelItem(pWidget)
        all_attrs = set(all_attrs)
        all_attrs = list(all_attrs)
        self.dlg.attributeBox.clear()
        for i in range(0, len(all_attrs)):
            self.dlg.attributeBox.addItem(all_attrs[i])

    def attrSelected(self):
        c_attr = self.dlg.attributeBox.currentText()
        for i in range(0, self.dlg.currentLayers.topLevelItemCount()):
            item = self.dlg.currentLayers.topLevelItem(i)
            if not type(item) == layerItem:
                for cWidget in item.children():
                    if c_attr in cWidget.text(0):
                        cWidget = changeCheckState(cWidget)

            else:
                if c_attr in item.text(0):
                    item = changeCheckState(item)

    def addToGenContour(self):
        for i in range(0, self.dlg.currentLayers.topLevelItemCount()):
            item = self.dlg.currentLayers.topLevelItem(i)
            if item.childCount() > 0:
                NewItem = QTreeWidgetItem(self.dlg.layersToDraw, item.text(0))
                NewItem.setText(0, item.text(0))
                for j in range(0, item.childCount()):
                    cWidget = item.child(j)
                    if cWidget.checkState(0) == Qt.Checked:
                        cWidget = layerItem(NewItem, cWidget.text(0),
                                            cWidget.layerId)
                        cWidget.setFlags(
                            cWidget.flags() ^ Qt.ItemIsUserCheckable)
                        NewItem.addChild(cWidget)
            else:
                if item.checkState(0) == Qt.Checked:
                    item = layerItem(None, item.text(0), item.layerId)
                    item.setFlags(item.flags() ^ Qt.ItemIsUserCheckable)
                    self.dlg.layersToDraw.addTopLevelItem(item)

    def removeFromAdded(self):
        c_item = self.dlg.layersToDraw.selectedItems()
        for i in range(0, len(c_item)):
            if c_item[i].childCount() > 0:
                idx = self.dlg.layersToDraw.indexOfTopLevelItem(c_item[i])
                self.dlg.layersToDraw.takeTopLevelItem(idx)
            else:
                idx = self.dlg.layersToDraw.indexOfTopLevelItem(c_item[i])
                if idx >= 0:
                    self.dlg.layersToDraw.takeTopLevelItem(idx)
                else:
                    parentItem = c_item[i].parent()
                    idx = self.dlg.layersToDraw.indexOfTopLevelItem(parentItem)
                    idx2 = self.dlg.layersToDraw.topLevelItem(
                        idx).indexOfChild(c_item[i])
                    self.dlg.layersToDraw.topLevelItem(idx).takeChild(idx2)

    def transferToContour(self):
        layersToDraw = list()
        for i in range(0, self.dlg.layersToDraw.topLevelItemCount()):
            p_item = self.dlg.layersToDraw.topLevelItem(i)
            if p_item.childCount() > 0:
                for j in range(0, p_item.childCount()):
                    c_item = p_item.child(j)
                    layersToDraw.append((c_item.text(0), c_item.layerId,
                                         c_item.outputFolder))
            else:
                try:
                    layerName = p_item.text(0)
                    layerId = p_item.layerId
                    outputFolder = p_item.outputFolder

                    layersToDraw.append((layerName, layerId, outputFolder))
                except(AttributeError):
                    pass

    def cleanSelected(self):
        self.dlg.layersToDraw.clear()

    def setOutputDir(self, assignedFolder):
        for i in range(0, self.dlg.layersToDraw.topLevelItemCount()):
            p_item = self.dlg.layersToDraw.topLevelItem(i)
            if p_item.childCount() > 0:
                for j in range(0, p_item.childCount()):
                    c_item = p_item.child(j)
                    if not c_item.outputFolder:
                        c_item.outputFolder = assignedFolder
            else:
                if not p_item.outputFolder:
                    p_item.outputFolder = assignedFolder

    def exportContour(self):
        pass

    def run(self):
        self.dlg.show()
        self.layerFromRegistry()
        result = self.dlg.exec_()
        if result == 1:
            folder = QFileDialog.getExistingDirectory()
            self.setOutputDir(folder)
