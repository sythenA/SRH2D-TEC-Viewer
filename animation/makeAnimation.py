
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog
from qgis.PyQt.QtGui import QPixmap, QIcon
from qgis.core import QgsMapLayerRegistry


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'animation.ui'))


class layerItem(QListWidgetItem):
    def __init__(self, layer, parent):
        super(layerItem, self).__init__(layer.name(), parent)
        self.layer = layer


class animationDiag(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(animationDiag, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        pixMap1 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-up.svg'))
        icon1 = QIcon(pixMap1)
        self.moveUpBtn.setIcon(icon1)
        self.moveUpBtn.setIconSize(self.moveUpBtn.size())

        pixMap2 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-down.svg'))
        icon2 = QIcon(pixMap2)
        self.moveDownBtn.setIcon(icon2)
        self.moveDownBtn.setIconSize(self.moveDownBtn.size())
        self.timeLapseEdit.setText(str(self.settings.value('frameTimeLapse')))

        self.registry = QgsMapLayerRegistry.instance()
        self.updateLayers()

        self.registry.legendLayersAdded.connect(self.newLayersAdded)
        self.registry.layersWillBeRemoved.connect(self.layersRemoved)
        self.moveUpBtn.clicked.connect(self.moveUp)
        self.moveDownBtn.clicked.connect(self.moveDown)

    def updateLayers(self):
        mapLayers = self.registry.mapLayers()
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

    def moveUp(self):
        item = self.layerList.currentItem()
        idx = self.layerList.currentRow()

        if item and idx-1 > 0:
            self.layerList.removeItemWidget(item)
            self.layerList.insertItem(idx-1, item)

    def moveDown(self):
        item = self.layerList.currentItem()
        idx = self.layerList.currentRow()

        if item and idx+1 < self.layerList.count():
            self.layerList.removeItemWidget(item)
            self.layerList.insertItem(idx+1, item)


class makeAnimation:
    def __init__(self, iface):
        self.iface = iface
        self.dlg = animationDiag(self.iface)
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass
