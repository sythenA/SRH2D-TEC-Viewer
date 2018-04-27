
from profilePlotDiag import profileViewerDialog
from ..tools.TECBoxItem import TECBoxItem, layerItem
from qgis.PyQt.QtGui import QWidget, QColor, QTreeWidgetItem
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.core import QgsProject, QgsMapLayer
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

        # profile settings
        self.activateDrawProfileCS()

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
        if self.TEC_Box:
            self.setLayerList(self.TEC_Box)
        else:
            self.layerFromRegistry()

        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

    def setLayerList(self, TEC_Container):
        for item in TEC_Container:
            self.dlg.TecFileList.addTopLevelItem(
                TECBoxItem(self.dlg.TecFileList, item))

    def layerFromRegistry(self):
        root = QgsProject.instance().layerTreeRoot()
        for node in root.children():
            if len(node.children()) > 0:
                pWidget = QTreeWidgetItem(self.dlg.TecFileList, node.name())
                for layer in node.children():
                    if layer.layer().layerType() == QgsMapLayer.RasterLayer():
                        attrName = layer.name()
                        attrLayerId = layer.layerId()

                        cWidget = layerItem(pWidget, attrName, attrLayerId)
                        pWidget.addChild(cWidget)
                self.dlg.TECfileList.addTopLevelItem(pWidget)
            else:
                attrName = node.name()
                attrLayerId = node.layerId()
                pWidget = layerItem(self.dlg.TecFileList, attrName, attrLayerId)
                self.dlg.TecFileList.addTopLevelItem(pWidget)
        self.activateDrawProfileCS()

    def setLayerState(self, item, idx):
        item.doAsState()

    def setToActive(self, item, idx):
        if type(item) == layerItem:
            item.setToActiveLayer()
