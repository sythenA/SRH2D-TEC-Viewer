
import os
from qgis.gui import QgsRubberBand, QgsVertexMarker
from qgis.core import QgsMapLayer, QgsProject, QgsMapLayerRegistry, QgsPoint
from qgis.core import QgsPointXY
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR, QSize, QLine, QRect
from qgis.PyQt.QtGui import QWidget, QColor, QListWidgetItem, QPen, QBrush
from qgis.PyQt.QtGui import QPainter, QPixmap, QIcon
from qgis.PyQt.QtSvg import QSvgGenerator
from .lineStyleDiag import lineStyleSelector
from .plotTool import plotTool
from .dataReaderTool import DataReaderTool
from random import randint


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

        self.dlg.activeLayerList.itemChanged.connect(self.plotProfiles)
        self.dlg.activeLayerList.itemDoubleClicked.connect(
            self.changeCurveStyle)

    def getProfile(self, pointstoDraw, toolRenderer):
        self.rubberbandbuf.reset()
        self.pointstoDraw = pointstoDraw

        # self.prepar_points(self.pointstoDraw)   # for mouse tracking
        # self.removeClosedLayers(self.dlg.mdl)
        if pointstoDraw is None:
            return

        plotTool().clearData(self.dlg.plotWidget, self.profiles)

        self.profiles = []

        layersList, TECfiles = self.layersSelected()
        # calculate profiles
        for i in range(0, len(layersList)):
            if layersList[i].type() == QgsMapLayer.VectorLayer:
                vec_profile, buffer, multipoly = DataReaderTool(
                ).dataVectorReaderTool(
                    self.iface, toolRenderer, layersList[i],
                    self.pointstoDraw)
                self.profiles.append(vec_profile)
                self.profiles[-1].update({'TECName': TECfiles[i]})
                self.rubberbandbuf.addGeometry(buffer, None)
                self.rubberbandbuf.addGeometry(multipoly, None)

            else:
                self.profiles.append(DataReaderTool().dataRasterReaderTool(
                    self.iface, toolRenderer, layersList[i],
                    self.pointstoDraw))
                self.profiles[-1].update({'TECName': TECfiles[i]})

        # plot profiles
        for i in range(0, len(self.profiles)):
            profileItem = profileListItem(self.profiles[i],
                                          self.dlg.activeLayerList)
            self.dlg.activeLayerList.addItem(profileItem)

        self.plotProfiles()
        # update the legend table

    def changeCurveStyle(self, item):
        selectorWindow = lineStyleSelector(self.iface, init_Color=item.color,
                                           init_LineStyle=item.lineStyle,
                                           init_Width=item.width)
        res = selectorWindow.run()
        if res:
            color = res[0]
            lineStyle = res[1]
            width = res[2]

            item.color = color
            item.lineStyle = lineStyle
            item.width = width
            item.genIcon()
            item.setStyle()
            self.plotProfiles()

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
        TECfiles = list()

        for i in range(0, TECs):
            TECitem = self.dlg.TecFileList.topLevelItem(i)
            TECName = TECitem.text(0)
            if TECitem.childCount() > 0:
                for j in range(0, TECitem.childCount()):
                    layerItem = TECitem.child(j)
                    if layerItem.checkState(0) == Qt.Checked:
                        layerId = layerItem.layerId
                        layer = QgsMapLayerRegistry.instance().mapLayer(
                            layerId)
                        activeLayers.append(layer)
                        TECfiles.append(TECName)
            else:
                if TECitem.checkState(0) == Qt.Checked:
                    layerId = TECitem.layerId
                    layer = QgsMapLayerRegistry.instance().mapLayer(layerId)
                    activeLayers.append(layer)
                    TECfiles.append(TECName)

        return activeLayers, TECfiles

    def updateProfileFromFeatures(self, layer, features, tool,
                                  plotProfile=True):
        """Updates self.profiles from given feature list.

        This function extracts the list of coordinates from the given
        feature set and calls updateProfil.
        This function also manages selection/deselection of features in the
        active layer to highlight the feature being profiled.
        """
        self.rubberbandbuf.reset()
        plotTool().clearData(self.dlg.plotWidget, self.profiles)
        self.dlg.activeLayerList.clear()

        pointstoDraw = []

        """
        # Remove selection from previous layer if it still exists
        previousLayer = QgsProject.instance().mapLayer(
                            self.previousLayerId)
        if previousLayer:
            previousLayer.removeSelection()

        if layer:
            self.previousLayerId = layer.id()
        else:
            self.previousLayerId = None"""

        if layer:
            layer.removeSelection()
            layer.select([f.id() for f in features])
            first_segment = True
            for feature in features:
                if first_segment:
                    k = 0
                    first_segment = False
                else:
                    k = 1
                while not feature.geometry().vertexAt(k) == QgsPoint(0, 0):
                    point2 = tool.toMapCoordinates(
                        layer, QgsPointXY(feature.geometry().vertexAt(k)))
                    pointstoDraw += [[point2.x(), point2.y()]]
                    k += 1
        self.updateProfile(pointstoDraw, tool, False, plotProfile)

    def updateProfile(self, points1, tool, removeSelection=True,
                      plotProfil=True):
        """Updates self.profiles from values in points1.

        This function can be called from updateProfilFromFeatures or from
        ProfiletoolMapToolRenderer (with a list of points from rubberband).
        """
        if removeSelection:
            # Be sure that we unselect anything in the previous layer.
            previousLayer = QgsProject.instance().mapLayer(
                                self.previousLayerId)
            if previousLayer:
                previousLayer.removeSelection()
        # replicate last point (bug #6680)
        # if points1:
        #    points1 = points1 + [points1[-1]]
        self.pointstoDraw = points1
        self.profiles = []

        # calculate profiles
        layersList, TECfiles = self.layersSelected()

        for i in range(0, len(layersList)):
            self.profiles.append(DataReaderTool().dataRasterReaderTool(
                self.iface, tool, layersList[i], self.pointstoDraw))
            self.profiles[-1].update({'TECName': TECfiles[i]})

        # plot profiles
        for i in range(0, len(self.profiles)):
            profileItem = profileListItem(self.profiles[i],
                                          self.dlg.activeLayerList)
            self.dlg.activeLayerList.addItem(profileItem)

        self.plotProfiles()

    def plotProfiles(self):
        self.dlg.plotWidget.clear()
        profileList = list()
        for i in range(0, self.dlg.activeLayerList.count()):
            item = self.dlg.activeLayerList.item(i)
            profileList.append(item.profile)
        plotTool().attachCurves(self.dlg.plotWidget, profileList)


QtCorlors = {1: Qt.black, 2: Qt.red, 3: Qt.darkRed, 4: Qt.green,
             5: Qt.darkGreen, 6: Qt.blue, 7: Qt.darkBlue, 8: Qt.cyan,
             9: Qt.darkCyan, 10: Qt.magenta, 11: Qt.darkMagenta, 12: Qt.yellow,
             13: Qt.darkYellow, 14: Qt.gray, 15: Qt.darkGray}


class profileListItem(QListWidgetItem):
    lineStyle = Qt.SolidLine

    def __init__(self, profile, parent):
        self.name = profile['TECName'] + '_' + profile['layer'].name()
        super(profileListItem, self).__init__(self.name, parent)
        self.profile = profile
        self.width = 3.
        self.color = QtCorlors[randint(1, 14)]
        self.setStyle()
        self.genIcon()

    def setStyle(self):
        self.Style = QPen(QBrush(self.color), self.width, style=self.lineStyle)
        self.profile.update({'style': self.Style})

    def genIcon(self):
        TECName = self.profile['TECName']
        svgName = os.path.join(os.path.dirname(__file__),
                               TECName + '_' + self.name + '.svg')
        pix = QSvgGenerator()
        pix.setFileName(svgName)
        pix.setSize(QSize(200, 100))
        painter = QPainter()
        painter.begin(pix)
        painter.setPen(Qt.NoPen)
        # Paint the background before draw the legend line.(Essential!!)
        painter.fillRect(QRect(0, 0, 200, 100), Qt.white)
        painter.setPen(QPen(self.color, self.width*3, self.lineStyle))
        # Draw icon
        painter.drawLine(QLine(0, 50, 200, 50))
        painter.end()

        pixmap = QPixmap(svgName)
        icon = QIcon(pixmap)
        self.icoName = svgName

        self.setIcon(icon)
