
import os
from qgis.gui import QgsRubberBand, QgsVertexMarker, QgsMapTool
from qgis.core import QgsMapLayer, QgsProject, QgsMapLayerRegistry, QgsPoint
from qgis.core import QgsPointXY
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR, QSize, QLine, QRect
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QWidget, QColor, QListWidgetItem, QPen, QBrush
from qgis.PyQt.QtGui import QPainter, QPixmap, QIcon, QFileDialog
from qgis.PyQt.QtSvg import QSvgGenerator
from .lineStyleDiag import lineStyleSelector
from .plotTool import plotTool
from .dataReaderTool import DataReaderTool
from random import randint
import xlwt


class profileSec(QWidget):
    def __init__(self, iface, profilePlotMain, parent=None):
        super(profileSec, self).__init__(parent)
        self.dlg = profilePlotMain.dlg
        self.iface = iface
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        self.rubberband = profilePlotMain.rubberband
        self.rubberbandbuf = profilePlotMain.rubberbandbuf
        self.rubberbandpoint = profilePlotMain.rubberbandpoint
        # dictionary where is saved the plotting data {"l":[l],"z":[z],
        # "layer":layer1, "curve":curve1}
        self.profiles = None

        self.dlg.activeLayerList.itemChanged.connect(self.plotProfiles)
        self.dlg.activeLayerList.itemDoubleClicked.connect(
            self.changeCurveStyle)

        self.dlg.moveForwardBtn.clicked.connect(self.moveForward)
        self.dlg.moveBackwardBtn.clicked.connect(self.moveBackward)
        self.dlg.exportPicBtn.clicked.connect(self.selectPlotExport)

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
        self.updateProfile(pointstoDraw, tool, plotProfile)

    def updateProfile(self, points1, tool, plotProfile=True):
        """Updates self.profiles from values in points1.

        This function can be called from updateProfilFromFeatures or from
        ProfiletoolMapToolRenderer (with a list of points from rubberband).
        """
        self.profiles = []

        # calculate profiles
        layersList, TECfiles = self.layersSelected()

        for i in range(0, len(layersList)):
            self.profiles.append(DataReaderTool().dataRasterReaderTool(
                self.iface, tool, layersList[i], points1))
            self.profiles[-1].update({'TECName': TECfiles[i]})

        # plot profiles
        for i in range(0, len(self.profiles)):
            profileItem = profileListItem(self.profiles[i],
                                          self.dlg.activeLayerList)
            self.dlg.activeLayerList.addItem(profileItem)

        if plotProfile:
            self.plotProfiles()

    def selectPlotExport(self):
        if self.dlg.batchChecker.checkState() == 2:
            layer = self.dlg.layerCombo.currentLayer()
            self.batchExportPlot(layer)
        else:
            self.exportPlot()

    def batchExportAsTxt(self, layer, f):
        features = layer.selectedFeatures()

        mapTool = QgsMapTool(self.iface.mapCanvas())
        FieldName = self.dlg.fieldCombo.currentField()

        for feature in features:
            title = feature[FieldName]
            if not title:
                title = 'profile'
            self.profiles = list()
            pointstoDraw = list()

            # Get feature geometry
            first_segment = True
            if first_segment:
                k = 0
                first_segment = False
            else:
                k = 1
            while not feature.geometry().vertexAt(k) == QgsPoint(0, 0):
                point2 = mapTool.toMapCoordinates(
                    layer, QgsPointXY(feature.geometry().vertexAt(k)))
                pointstoDraw += [[point2.x(), point2.y()]]
                k += 1
            self.updateProfile(pointstoDraw, mapTool, False)
            if self.profiles:
                plotTool().exportToTxt(self.profiles, f, str(title))
                plotTool().clearData(self.dlg.plotWidget, self.profiles)
                self.dlg.activeLayerList.clear()

    def batchExportAsCsv(self, layer, f):
        features = layer.selectedFeatures()

        mapTool = QgsMapTool(self.iface.mapCanvas())
        FieldName = self.dlg.fieldCombo.currentField()

        for feature in features:
            title = feature[FieldName]
            if not title:
                title = 'profile'
            self.profiles = list()
            pointstoDraw = list()

            # Get feature geometry
            first_segment = True
            if first_segment:
                k = 0
                first_segment = False
            else:
                k = 1
            while not feature.geometry().vertexAt(k) == QgsPoint(0, 0):
                point2 = mapTool.toMapCoordinates(
                    layer, QgsPointXY(feature.geometry().vertexAt(k)))
                pointstoDraw += [[point2.x(), point2.y()]]
                k += 1
            self.updateProfile(pointstoDraw, mapTool, False)
            if self.profiles:
                plotTool().exportToCsv(self.profiles, f, str(title))
                plotTool().clearData(self.dlg.plotWidget, self.profiles)
                self.dlg.activeLayerList.clear()

    def batchExportAsXls(self, layer, Wb):
        features = layer.selectedFeatures()

        mapTool = QgsMapTool(self.iface.mapCanvas())
        FieldName = self.dlg.fieldCombo.currentField()

        for feature in features:
            title = feature[FieldName]
            if not title:
                title = 'profile'
            sh = Wb.add_sheet(str(title))
            self.profiles = list()
            pointstoDraw = list()

            # Get feature geometry
            first_segment = True
            if first_segment:
                k = 0
                first_segment = False
            else:
                k = 1
            while not feature.geometry().vertexAt(k) == QgsPoint(0, 0):
                point2 = mapTool.toMapCoordinates(
                    layer, QgsPointXY(feature.geometry().vertexAt(k)))
                pointstoDraw += [[point2.x(), point2.y()]]
                k += 1
            self.updateProfile(pointstoDraw, mapTool, False)
            if self.profiles:
                plotTool().exportToXls(self.profiles, sh, title)
                plotTool().clearData(self.dlg.plotWidget, self.profiles)
                self.dlg.activeLayerList.clear()

    def moveForward(self):
        idx = self.dlg.activeLayerList.currentRow()
        citem = self.dlg.activeLayerList.takeItem(idx)

        if idx-1 < 0:
            idx = 1
        self.dlg.activeLayerList.insertItem(idx-1, citem)

        self.plotProfiles()

    def moveBackward(self):
        idx = self.dlg.activeLayerList.currentRow()
        citem = self.dlg.activeLayerList.takeItem(idx)

        if idx+1 > self.dlg.activeLayerList.count():
            idx = self.dlg.activeLayerList.count() - 1
        self.dlg.activeLayerList.insertItem(idx+1, citem)

        self.plotProfiles()

    def plotProfiles(self):
        self.dlg.plotWidget.clear()
        profileList = list()
        total = self.dlg.activeLayerList.count()
        for i in range(total-1, -1, -1):
            item = self.dlg.activeLayerList.item(i)
            profileList.append(item.profile)
        plotTool().attachCurves(self.dlg.plotWidget, profileList)

    def exportText(self):
        projFolder = self.settings.value('projFolder')
        if self.settings.value('profileTextExport') == '.txt':
            exportFile = QFileDialog.getSaveFileName(
                directory=projFolder, filter='Text files(*.txt)')
            if self.profiles and exportFile:
                f = open(exportFile, 'w')
                if self.dlg.batchChecker.checkState() == 0:
                    plotTool().exportToTxt(self.profiles)

                elif self.dlg.batchChecker.checkState() == 2:
                    layer = self.dlg.layerCombo.currentLayer()
                    self.batchExportAsTxt(layer, f)
                f.close()
        elif self.settings.value('profileTextExport') == '.csv':
            exportFile = QFileDialog.getSaveFileName(
                directory=projFolder, filter='Text files(*.csv)')
            if self.profiles and exportFile:
                f = open(exportFile, 'w')
                if self.dlg.batchChecker.checkState() == 0:
                    plotTool().exportToCsv(self.profiles, f)
                elif self.dlg.batchChecker.checkState() == 2:
                    layer = self.dlg.layerCombo.currentLayer()
                    self.batchExportAsCsv(layer, f)
                f.close()

        elif self.settings.value('profileTextExport') == '.xls':
            exportFile = QFileDialog.getSaveFileName(
                directory=projFolder, filter='Excel Workbook(*.xls)')
            if self.profiles and exportFile:
                wb = xlwt.Workbook()
                if self.dlg.batchChecker.checkState() == 0:
                    sh = wb.add_sheet('profile')
                    plotTool().exportToXls(self.profiles, sh)
                elif self.dlg.batchChecker.checkState() == 2:
                    layer = self.dlg.layerCombo.currentLayer()
                    self.batchExportAsXls(layer, wb)
                wb.save(exportFile)

    def exportPlot(self, folder=None, name=None, title=None):
        if self.settings.value('profilePlotExport') == '.png':
            plotWidget = self.dlg.plotWidget
            plotTool().outPNG(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.jpg':
            plotWidget = self.dlg.plotWidget
            plotTool().outJPG(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.bmp':
            plotWidget = self.dlg.plotWidget
            plotTool().outBMP(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.svg':
            plotWidget = self.dlg.plotWidget
            plotTool().outSVG(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.tiff':
            plotWidget = self.dlg.plotWidget
            plotTool().outTIF(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.xbm':
            plotWidget = self.dlg.plotWidget
            plotTool().outXBM(plotWidget, folder, name, title)
        elif self.settings.value('profilePlotExport') == '.xpm':
            plotWidget = self.dlg.plotWidget
            plotTool().outXPM(plotWidget, folder, name, title)

    def batchExportPlot(self, layer):
        features = layer.selectedFeatures()

        mapTool = QgsMapTool(self.iface.mapCanvas())
        FieldName = self.dlg.fieldCombo.currentField()

        projFolder = self.settings.value('projFolder')
        outputFolder = QFileDialog.getExistingDirectory(
            directory=projFolder,
            caption='Choose the folder to export profile plots')

        if outputFolder:
            for feature in features:
                title = feature[FieldName]
                if not title:
                    title = 'profile'
                self.profiles = list()
                pointstoDraw = list()

                # Get feature geometry
                first_segment = True
                if first_segment:
                    k = 0
                    first_segment = False
                else:
                    k = 1
                while not feature.geometry().vertexAt(k) == QgsPoint(0, 0):
                    point2 = mapTool.toMapCoordinates(
                        layer, QgsPointXY(feature.geometry().vertexAt(k)))
                    pointstoDraw += [[point2.x(), point2.y()]]
                    k += 1
                self.updateProfile(pointstoDraw, mapTool, False)
                if self.profiles:
                    self.exportPlot(folder=outputFolder,
                                    name=str(feature.id()).zfill(3),
                                    title=str(title))
                    plotTool().clearData(self.dlg.plotWidget, self.profiles)
                    self.dlg.activeLayerList.clear()


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
