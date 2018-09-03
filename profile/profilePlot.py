
from profilePlotDiag import profileViewerDialog
from ..tools.TECBoxItem import TECBoxItem, layerItem
from qgis.PyQt.QtGui import QWidget, QColor, QTreeWidgetItem, QCursor
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.core import QgsProject, QgsMapLayer, QgsMapLayerRegistry
from qgis.PyQt.QtCore import Qt, QSettings
from drawTempLayer import plotCSTool
from callMapTool import profileSec


class profilePlot(QWidget):
    def __init__(self, iface, projFolder=None, parent=None,
                 TEC_Box=None):
        QWidget.__init__(self, parent)

        self.iface = iface
        self.dlg = profileViewerDialog()
        self.TEC_Box = TEC_Box

        #  ---Signals Connections---
        self.dlg.TecFileList.itemChanged.connect(self.setLayerState)
        self.dlg.TecFileList.itemActivated.connect(self.setToActive)
        self.registry = QgsMapLayerRegistry.instance()

        self.iface = iface

        # the rubberband
        self.polygon = False
        self.rubberband = QgsRubberBand(self.iface.mapCanvas(), self.polygon)
        self.rubberband.setWidth(2)
        self.rubberband.setColor(QColor(Qt.red))
        self.rubberbandpoint = QgsVertexMarker(self.iface.mapCanvas())
        self.rubberbandpoint.setColor(QColor(Qt.red))
        self.rubberbandpoint.setIconSize(5)
        self.rubberbandpoint.setIconType(QgsVertexMarker.ICON_BOX)
        # or ICON_CROSS, ICON_X
        self.rubberbandpoint.setPenWidth(3)

        self.rubberbandbuf = QgsRubberBand(self.iface.mapCanvas())
        self.rubberbandbuf.setWidth(1)
        self.rubberbandbuf.setColor(QColor(Qt.blue))
        # remember repository for saving
        if QSettings().value("projFolder") != '':
            self.loaddirectory = QSettings().value(
                "projFolder")
        else:
            self.loaddirectory = ''

        self.profileSec = profileSec(self.iface, self)

        # profile settings
        registry = QgsMapLayerRegistry.instance()
        registry.legendLayersAdded.connect(self.layerFromRegistry)
        self.dlg.methodSelector.currentIndexChanged.connect(
            self.changeOfMethod)
        self.dlg.exportTextBtn.clicked.connect(self.exportText)

    def activateDrawProfileCS(self):
        # Save the standard mapttool for restoring it at the end
        self.saveTool = self.iface.mapCanvas().mapTool()
        # Listeners of mouse
        self.toolrenderer = plotCSTool(self)
        self.toolrenderer.connectTool()
        # init the mouse listener comportement and save the classic to restore
        # it on quit
        self.iface.mapCanvas().setMapTool(self.toolrenderer.tool)

    def run(self):
        self.activateDrawProfileCS()
        self.cursor = QCursor(Qt.CrossCursor)
        if self.TEC_Box:
            self.setLayerList(self.TEC_Box)
        else:
            self.layerFromRegistry()

        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

    def exportText(self):
        profileSec = self.profileSec
        profileSec.exportText()

    def setLayerList(self, TEC_Container):
        for item in TEC_Container:
            self.dlg.TecFileList.addTopLevelItem(
                TECBoxItem(self.dlg.TecFileList, item))

    def layerFromRegistry(self):
        self.dlg.TecFileList.clear()
        try:
            root = QgsProject.instance().layerTreeRoot()
        except(AttributeError):
            return

        for node in root.children():
            if len(node.children()) > 0:
                pWidget = QTreeWidgetItem(self.dlg.TecFileList)
                pWidget.setText(0, str(node.name()))
                for layer in node.children():
                    _layer = self.registry.mapLayer(layer.layerId())
                    if _layer.type() == QgsMapLayer.RasterLayer:
                        attrName = _layer.name()
                        attrLayerId = layer.layerId()

                        cWidget = layerItem(pWidget, attrName, attrLayerId)
                        pWidget.addChild(cWidget)
                self.dlg.TecFileList.addTopLevelItem(pWidget)
            else:
                attrName = node.name()
                try:
                    attrLayerId = node.layerId()
                    layer = self.registry.mapLayer(attrLayerId)
                    if layer.type() == QgsMapLayer.RasterLayer:
                        pWidget = layerItem(self.dlg.TecFileList, attrName,
                                            attrLayerId)
                        self.dlg.TecFileList.addTopLevelItem(pWidget)

                except(AttributeError):
                    attrLayerId = ''

    def setLayerState(self, item, idx):
        try:
            item.doAsState()
        except(AttributeError):
            pass

    def setToActive(self, item, idx):
        if type(item) == layerItem:
            item.setToActiveLayer()

    def changeOfMethod(self, idx):
        if idx == 0:
            self.toolrenderer.changeToHandDraw()
            self.iface.mapCanvas().setCursor(QCursor(Qt.CrossCursor))
        elif idx == 1:
            layer = self.dlg.layerCombo.currentLayer()
            self.iface.setActiveLayer(layer)
            self.iface.mapCanvas().setCursor(QCursor(Qt.PointingHandCursor))
            self.toolrenderer.changeToSelectLine()
