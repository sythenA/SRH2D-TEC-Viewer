
from PyQt4.QtGui import QTreeWidgetItem
from PyQt4.QtCore import Qt
from qgis.core import QgsMapLayerRegistry
from qgis.utils import iface


class TECBoxItem(QTreeWidgetItem):
    def __init__(self, parent, TECBox):
        super(TECBoxItem, self).__init__(parent, TECBox.fileName)
        self.childWidget(TECBox)
        self.setText(0, TECBox.fileName)
        self.setCheckState(0, Qt.Checked)

    def childWidget(self, TECBox):
        keys = TECBox.attrs.keys()
        for key in keys:
            self.addChild(layerItem(self, key, TECBox.attrs[key]))

    def hideAllLayers(self):
        N = self.childCount()
        for i in range(0, N):
            self.child(i).setLayerInvisible()
            self.child(i).setCheckState(0, Qt.Unchecked)
            self.child(i).setFlags(
                self.child(i).flags() ^ Qt.ItemIsUserCheckable)

    def showAllLayers(self):
        N = self.childCount()
        for i in range(0, N):
            self.child(i).setLayerVisible()
            self.child(i).setCheckState(0, Qt.Checked)
            self.child(i).setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

    def doAsState(self):
        if self.checkState(0) == Qt.Checked:
            self.showAllLayers()
        else:
            self.hideAllLayers()


class layerItem(QTreeWidgetItem):
    def __init__(self, parent, attrName, layerId):
        super(layerItem, self).__init__(parent, attrName)

        self.layerId = layerId
        self.setCheckState(0, Qt.Checked)
        self.setText(0, attrName)
        self.outputFolder = ''

    def setLayerVisible(self):
        ml = QgsMapLayerRegistry.instance().mapLayer(self.layerId)
        iface.legendInterface().setLayerVisible(ml, True)

    def setLayerInvisible(self):
        ml = QgsMapLayerRegistry.instance().mapLayer(self.layerId)
        iface.legendInterface().setLayerVisible(ml, False)

    def doAsState(self):
        if self.checkState(0) == Qt.Checked:
            self.setLayerVisible()
        else:
            self.setLayerInvisible()

    def setToActiveLayer(self):
        mlayer = QgsMapLayerRegistry.instance().mapLayer(self.layerId)
        iface.setActiveLayer(mlayer)
