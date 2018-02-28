
from profilePlotDiag import profileViewerDialog
from ..tools.TECBoxItem import TECBoxItem, layerItem
from qgis.PyQt.QtGui import QWidget, QColor
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import Qt, QSettings
from drawTempLayer import plotCSTool


class profilePlot(QWidget):
    def __init__(self, iface, TEC_Container, projFolder, parent=None):
        QWidget.__init__(self, parent)

        self.iface = iface
        self.dlg = profileViewerDialog()
        self.setLayerList(TEC_Container)

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
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

    def setLayerList(self, TEC_Container):
        for item in TEC_Container:
            self.dlg.TecFileList.addTopLevelItem(
                TECBoxItem(self.dlg.TecFileList, item))

    def setLayerState(self, item, idx):
        item.doAsState()

    def setToActive(self, item, idx):
        if type(item) == layerItem:
            item.setToActiveLayer()

