
import os
import subprocess
import pip
from conExportDialog import conExportDiag
from qgis.core import QgsMapLayerRegistry, QGis, QgsMapLayer
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsGenericProjectionSelector
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog
from qgis.PyQt.QtCore import Qt, QSettings
from ..tools.toUnicode import toUnicode


installed_packages = pip.get_installed_distributions()
installed_packages = sorted(["%s" % i.key for i in installed_packages])
if "simplekml" not in installed_packages:
    orgCwd = os.getcwd()
    inst_folder = os.path.join(os.path.dirname(__file__), 'simplekml')
    inst_folder = toUnicode(inst_folder)
    os.chdir(inst_folder)
    subprocess.call(['python', 'setup.py', 'install'])
    os.chdir(orgCwd)
    import simplekml
else:
    import simplekml


class contourLayerItem(QListWidgetItem):
    def __init__(self, name, registry, layerId, crs):
        super(contourLayerItem, self).__init__(name)
        self.setCheckState(Qt.Unchecked)
        self.name = name
        self.registry = registry
        self.layerId = layerId
        self.crs = crs
        self.exportFolder = None

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
        if os.path.isdir(os.path.join(folder, self.name)):
            subprocess.call(['RD', os.path.join(folder, self.name)],
                            shell=False)
            os.mkdir(os.path.join(folder, self.name))
        else:
            os.mkdir(os.path.join(folder, self.name))

        os.chdir(os.path.join(folder, self.name))
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
                        name=str(level), coords=lineGeo)
                    ls.style.linestyle.width = 2.5
        os.chdir(folder)
        kml.save(self.name + u'.kml')
        os.chdir(orgCwd)


class kmlExport:
    def __init__(self, iface):
        self.dlg = conExportDiag()
        self.registry = QgsMapLayerRegistry.instance()
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        if self.settings.value('kmlCrs'):
            self.kmlCrs = QgsCoordinateReferenceSystem(
                self.settings.value('kmlCrs'), crsType)
        else:
            self.kmlCrs = QgsCoordinateReferenceSystem(
                self.settings.value('crs'), crsType)

        self.dlg.selectGeoRefBtn.clicked.connect(self.setGeoRef)
        self.dlg.closeWindow.connect(self.breakConnection)

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
