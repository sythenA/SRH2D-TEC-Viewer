
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.core import QgsMapLayer, QgsProject, QgsMapLayerRegistry
from qgis.PyQt.QtCore import Qt, QSettings, QT_VERSION_STR
from qgis.PyQt.QtGui import QWidget, QColor
from .plotTool import plotTool
from .dataReaderTool import DataReaderTool


class profileSec(QWidget):
    def __init__(self, iface, dialog, parent=None):
        super(profileSec, self).__init__(parent)
        self.dlg = dialog
        self.iface = iface

        self.rubberband = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberband.setWidth(2)
        self.rubberband.setColor(QColor(Qt.red))
        self.rubberbandpoint = QgsVertexMarker(self.iface.mapCanvas())
        self.rubberbandpoint.setColor(QColor(Qt.red))
        self.rubberbandpoint.setIconSize(5)
        self.rubberbandpoint.setIconType(QgsVertexMarker.ICON_BOX)
        self.rubberbandpoint.setPenWidth(3)

        self.rubberbandbuf = QgsRubberBand(self.iface.mapCanvas())
        self.rubberbandbuf.setWidth(1)
        self.rubberbandbuf.setColor(QColor(Qt.blue))
        # dictionary where is saved the plotting data {"l":[l],"z":[z],
        # "layer":layer1, "curve":curve1}
        self.profiles = None

    def getProfile(self, points1, toolRenderer, vertline=True):
        self.rubberbandbuf.reset()
        self.pointstoDraw = points1

        # self.prepar_points(self.pointstoDraw)   # for mouse tracking
        # self.removeClosedLayers(self.dlg.mdl)
        if self.pointstoDraw is None:
            return

        plotTool().clearData(self.dlg.plotWidget, self.profiles)

        self.profiles = []

        if vertline:      # Plotting vertical lines at the node of polyline draw
            plotTool().drawVertLine(self.dlg.plotWidget, self.pointstoDraw)

        layersList = self.layersSelected()
        self.iface.messageBar().pushMessage(str(len(layersList)))
        # calculate profiles
        for i in range(0, len(layersList)):
            if layersList[i].type() == QgsMapLayer.VectorLayer:
                vec_profile, buffer, multipoly = DataReaderTool().dataVectorReaderTool(
                    self.iface, toolRenderer, layersList[i],
                    self.pointstoDraw)
                self.profiles.append(vec_profile)
                self.rubberbandbuf.addGeometry(buffer, None)
                self.rubberbandbuf.addGeometry(multipoly, None)

            else:
                self.profiles.append(DataReaderTool().dataRasterReaderTool(
                    self.iface, toolRenderer, layersList[i],
                    self.pointstoDraw))

        # plot profiles
        plotTool().attachCurves(self.dlg.plotWidget, self.profiles)
        # plotTool().reScalePlot(self.dlg, self.profiles)
        # update the legend table
        # self.dlg.updateCoordinateTab()

        # Mouse tracking(pyGraph Only)
        """
        if self.doTracking:
            self.rubberbandpoint.show()
        self.enableMouseCoordonates(self.dlg.plotlibrary)"""

    def removeClosedLayers(self, model1):
        qgisLayerNames = []
        if int(QT_VERSION_STR[0]) == 4:    # qgis2
            qgisLayerNames = [layer.name() for layer in
                              self.iface.legendInterface().layers()]
            """
            for i in range(0, self.iface.mapCanvas().layerCount()):
                    qgisLayerNames.append(self.iface.mapCanvas().layer(i).name())
            """
        elif int(QT_VERSION_STR[0]) == 5:    # qgis3
            qgisLayerNames = [layer.name() for layer in
                              QgsProject().instance().mapLayers().values()]

        for i in range(0, model1.rowCount()):
            layerName = model1.item(i, 2).data(Qt.EditRole)
            if layerName not in qgisLayerNames:
                self.dockwidget.removeLayer(i)
                self.removeClosedLayers(model1)
                break

    def layersSelected(self):
        TECs = self.dlg.TecFileList.topLevelItemCount()
        activeLayers = list()

        for i in range(0, TECs):
            TECitem = self.dlg.TecFileList.topLevelItem(i)
            for j in range(0, TECitem.childCount()):
                layerItem = TECitem.child(j)
                if layerItem.checkState(0) == Qt.Checked:
                    layerId = layerItem.layerId
                    layer = QgsMapLayerRegistry.instance().mapLayer(layerId)
                    activeLayers.append(layer)

        return activeLayers
