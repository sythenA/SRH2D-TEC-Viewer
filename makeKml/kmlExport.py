
import os
import subprocess
from conExportDialog import conExportDiag
from qgis.core import QgsMapLayerRegistry, QGis, QgsMapLayer
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsGenericProjectionSelector
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog
from qgis.PyQt.QtCore import Qt, QSettings
import simplekml
from ..tools.toUnicode import toUnicode


class contourLayerItem(QListWidgetItem):
    def __init__(self, name, registry, layerId, crs):
        super(contourLayerItem, self).__init__(name)
        self.setCheckState(Qt.Unchecked)
        self.name = name
        self.registry = registry
        self.layerId = layerId
        self.crs = crs
        self.exportFolder = None
        self.selectAll = 0

    def getConLevel(self):
        layer = self.registry.mapLayer(self.layerId)

        conValues = list()
        for feature in layer.getFeatures():
            conValues.append(feature['VALUE'])
        conValues = set(conValues)
        self.conValues = sorted(list(conValues))

    def exportToKml(self, folder):
        folder = toUnicode(folder)
        orgCwd = os.getcwd()
        if os.path.isdir(toUnicode(os.path.join(folder, self.name))):
            subprocess.call(['RD', toUnicode(os.path.join(folder, self.name))],
                            shell=False)
            os.mkdir(toUnicode(os.path.join(folder, self.name)))
        else:
            os.mkdir(toUnicode(os.path.join(folder, self.name)))

        os.chdir(toUnicode(os.path.join(folder, self.name)))
        kml = simplekml.Kml()
        layer = self.registry.mapLayer(self.layerId)
        for level in self.conValues:
            fold = kml.newfolder(name=str(level))
            for feature in layer.getFeatures():
                if feature['VALUE'] == level:
                    layerCrs = layer.crs()
                    tarCrs = self.crs
                    tr = QgsCoordinateTransform(layerCrs, tarCrs)
                    featureGeo = feature.geometry()
                    featureGeo.transform(tr)
                    lineGeo = featureGeo.asPolyline()
                    ls = fold.newlinestring(
                        name='{:10.3f}'.format(float(level)).lstrip(),
                        coords=lineGeo)
                    ls.style.linestyle.width = 2.5
        os.chdir(toUnicode(folder))
        kml.save(toUnicode(self.name + u'.kml'))
        os.chdir(toUnicode(orgCwd))


class kmlExport:
    def __init__(self, iface):
        self.dlg = conExportDiag()
        self.registry = QgsMapLayerRegistry.instance()
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')
        self.selectAll = 0

        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        if self.settings.value('kmlCrs'):
            self.kmlCrs = QgsCoordinateReferenceSystem(
                self.settings.value('kmlCrs'), crsType)
        else:
            if self.settings.value('crs'):
                crs = self.settings.value('crs')
            else:
                crs = 3826
            self.kmlCrs = QgsCoordinateReferenceSystem(crs, crsType)

        self.dlg.selectGeoRefBtn.clicked.connect(self.setGeoRef)
        self.dlg.closeWindow.connect(self.breakConnection)
        self.dlg.selectAllBtn.clicked.connect(self.selectAllinList)

    def setGeoRef(self):
        generic_projection_selector = QgsGenericProjectionSelector()
        generic_projection_selector.exec_()

        crsId = generic_projection_selector.selectedCrsId()
        if crsId:
            crsType = QgsCoordinateReferenceSystem.InternalCrsId
            self.kmlCrs = QgsCoordinateReferenceSystem(crsId, crsType)
            self.settings.setValue('kmlCrs', crsId)

            for i in range(0, self.dlg.conLayerList.count()):
                item = self.dlg.conLayerList.item(i)
                item.crs = self.kmlCrs

    def updateLayers(self):
        self.dlg.conLayerList.clear()
        layers = self.registry.mapLayers()
        for layerId in layers.keys():
            layer = self.registry.mapLayer(layerId)
            if layer.LayerType() == QgsMapLayer.VectorLayer:
                try:
                    if layer.geometryType() == QGis.Line:
                        conItem = contourLayerItem(layer.name(), self.registry,
                                                   layerId, self.kmlCrs)
                        conItem.getConLevel()
                        self.dlg.conLayerList.addItem(conItem)
                except:
                    pass
            else:
                pass

    def selectAllinList(self):
        for i in range(0, self.dlg.conLayerList.count()):
            item = self.dlg.conLayerList.item(i)
            if self.selectAll == 0:
                if item.checkState() == Qt.Unchecked:
                    item.setCheckState(Qt.Checked)
            else:
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
        if self.selectAll == 1:
            self.selectAll = 0
        elif self.selectAll == 0:
            self.selectAll = 1

    def run(self):
        self.dlg.show()
        self.updateLayers()
        self.registry.layersAdded.connect(self.updateLayers)
        self.registry.layerRemoved.connect(self.updateLayers)
        result = self.dlg.exec_()
        if result == 1:
            folder = QFileDialog.getExistingDirectory()
            self.exportItems(toUnicode(folder))

    def breakConnection(self):
        try:
            self.registry.layersAdded.disconnect()
        except(TypeError):
            pass
        try:
            self.registry.layersRemoved.disconnect()
        except(TypeError):
            pass

    def exportItems(self, folder):
        folder = toUnicode(folder)
        for i in range(0, self.dlg.conLayerList.count()):
            item = self.dlg.conLayerList.item(i)
            if item.checkState() == Qt.Checked:
                item.exportToKml(folder)
