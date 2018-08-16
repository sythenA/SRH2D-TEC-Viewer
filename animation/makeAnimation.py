
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog
from qgis.core import QgsMapLayerRegistry


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'animation.ui'))


class layerItem(QListWidgetItem):
    def __init__(self, layer, parent):
        super(layerItem, self).__init__(layer.name(), parent)
        self.layer = layer


class animationDiag(QtGui.Dialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(animationDiag, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        self.registry = QgsMapLayerRegistry.instance()
        self.updateLayers()

        self.registry.legendLayersAdded(self.newLayersAdded)
        self.registry.layersWillBeRemoved(self.layersRemoved)

    def updateLayer(self):
        mapLayers = self.registry.mapLayer()
        if mapLayers:
            for layerId in mapLayers.keys():
                layer = self.registry.mapLayer(layerId)
                item = layerItem(layer, self.layerList)
                self.layerList.addItem(item)

    def newLayersAdded(self, newLayers):
        if newLayers:
            for layer in newLayers:
                item = layerItem(layer, self.layerList)
                self.layerList.addItem(item)

    def layersRemoved(self, removedLayers):
        if removedLayers:
            for layer in removedLayers:
                layerName = layer.name()
                itemList = self.layerList.findItems(layerName,
                                                    Qt.MatchExactly)
                if itemList:
                    for item in itemList:
                        self.layerList.removeItemWidget(item)

    def run(self):
        self.show()
        result = self.exec_()
        if result:
            pass
