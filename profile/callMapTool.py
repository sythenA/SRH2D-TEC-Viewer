
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.core import QgsMapLayer
from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QWidget, QColor
from plotTool import plotTool
from dataReaderTool import DataReaderTool


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

    def startProfileDraw(self):
        self.saveTool = self.iface.mapCanvas().mapTool()

    def getProfile(self, points1, vertline=True):
        self.disableMouseCoordonates()
        self.rubberbandbuf.reset()
        self.pointstoDraw = points1

        # self.prepar_points(self.pointstoDraw)   # for mouse tracking
        self.removeClosedLayers(self.dlg.mdl)
        if self.pointstoDraw is None:
            return

        plotTool().clearData(self.dlg, self.profiles)

        self.profiles = []

        if vertline:      # Plotting vertical lines at the node of polyline draw
            plotTool().drawVertLine(self.dlg, self.pointstoDraw)

        # calculate profiles
        for i in range(0, self.dlg.mdl.rowCount()):
            self.profiles.append(
                {"layer": self.dlg.mdl.item(i, 5).data(Qt.EditRole)})
            self.profiles[i]["band"] = self.dlg.mdl.item(i, 3).data(Qt.EditRole)
            if (self.dlg.mdl.item(i, 5).data(Qt.EditRole).type() ==
                    QgsMapLayer.VectorLayer):
                self.profiles[i], buffer, multipoly = DataReaderTool().dataVectorReaderTool(
                    self.iface, self.toolrenderer.tool, self.profiles[i],
                    self.pointstoDraw,
                    float(self.dlg.mdl.item(i, 4).data(Qt.EditRole)))
                self.rubberbandbuf.addGeometry(buffer, None)
                self.rubberbandbuf.addGeometry(multipoly, None)

            else:
                self.profiles[i] = DataReaderTool().dataRasterReaderTool(
                    self.iface, self.toolrenderer.tool, self.profiles[i],
                    self.pointstoDraw, self.dlg.checkBox.isChecked())

        # plot profiles
        plotTool().attachCurves(self.dlg, self.profiles, self.dlg.mdl)
        plotTool().reScalePlot(self.dlg, self.profiles)
        # update the legend table
        # self.dlg.updateCoordinateTab()
        # Mouse tracking

        if self.doTracking:
            self.rubberbandpoint.show()
        self.enableMouseCoordonates(self.dlg.plotlibrary)
