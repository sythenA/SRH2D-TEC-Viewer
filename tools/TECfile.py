
from ..TECViewer_dialog import Settings
from PyQt4.QtGui import QListWidgetItem
from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerRegistry
from qgis.core import QgsFields, QgsField, QgsProject, QgsRasterLayer, QGis
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsFeature
from qgis.core import QgsGeometry, QgsStyleV2, QgsRasterBandStats
from qgis.core import QgsColorRampShader, QgsSingleBandPseudoColorRenderer
from qgis.core import QgsRasterShader
from osgeo import osr, gdal
from gdalconst import GA_Update
from PyQt4.QtCore import QVariant, QFileInfo
from math import ceil
import re
import subprocess
import os
import processing


class TECfile(QListWidgetItem):
    def __init__(self, parent, widgetType, filePath, iface, setting=Settings):
        super(TECfile, self).__init__(parent, widgetType)
        self.filePath = filePath
        self.fileName = os.path.basename(filePath)
        self.headerLinesCount = 0
        self.iface = iface
        self.TECTile = ''
        self.setting = setting
        self.variables = list()
        self.composition = dict()
        self.variableType = list()
        self.readTEC(filePath)
        self.outDir = ''
        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        crs = QgsCoordinateReferenceSystem(3826, refId)
        self.crs = crs
        self.iface = ''

        self.setText(os.path.basename(filePath))

    def readTEC(self, filePath):
        f = open(filePath)
        dat = f.readlines()
        self.getVariables(dat)
        self.dat = dat

    def loadTEC(self):
        self.readVariables(self.dat)

        for i in range(0, len(self.variables[3]['Water_Elev_m'])):
            if float(self.variables[3]['Water_Elev_m'][i]) == -999.0:
                self.variables[3][
                    'Water_Elev_m'][i] = self.variables[2]['Bed_Elev_meter'][i]
        self.makeMeshLayer()
        self.makeSieve()
        self.genNodeLayer()

    def export(self):
        self.outDir = os.path.join(self.outDir,
                                   self.fileName.replace('.dat', ''))
        if os.path.isdir(self.outDir):
            subprocess.call(['cmd', '/c', 'RD', '/S', '/Q', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir',
                             os.path.join(self.outDir, 'supplements')])
        else:
            subprocess.call(['cmd', '/c', 'mkdir', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir',
                             os.path.join(self.outDir, 'supplements')])
        self.loadTEC()
        group = QgsProject.instance().layerTreeRoot().addGroup(self.fileName)

        self.contentLayers = list()
        for attr in self.attributes:
            if attr[1] == 1:
                self.makeContentLayers(attr[0])
                if len(attr[0]) > 10:
                    rasterName = attr[0][0:10]
                else:
                    rasterName = attr[0]
                rasterPath = os.path.join(self.outDir, rasterName + '.tif')
                baseName = QFileInfo(rasterPath).baseName()
                rasterLayer = QgsRasterLayer(rasterPath, baseName)
                rasMapLayer = QgsMapLayerRegistry.instance().addMapLayer(
                    rasterLayer, False)
                self.contentLayers.append([attr[0], rasMapLayer.id()])
                group.addLayer(rasterLayer)

    def attributeList(self):
        attributes = self.attributes
        _attrs = list()
        for i in range(2, len(attributes)):
            _attrs.append([attributes[i], 0])
        self.attributes = _attrs

    def getVariables(self, dat):
        def readDat(dat, title, _variable, ZONE, DT):
            mode = 0
            lineCount = 0
            for line in dat:
                if line.startswith(' TITLE'):
                    mode = 0
                elif line.startswith(' VARIABLES'):
                    mode = 1
                elif line.startswith(' ZONE'):
                    mode = 2
                elif line.startswith(' DT'):
                    mode = 3
                elif line.endswith(')\n'):
                    mode = 4

                if mode == 0:
                    title.append(line)
                elif mode == 1:
                    _variables.append(line)
                elif mode == 2:
                    ZONE.append(line)
                elif mode == 3 or mode == 4:
                    DT.append(line)
                    if line.endswith(')\n'):
                        mode = 5
                else:
                    return (title, _variable, ZONE, DT, lineCount)
                lineCount += 1

        title = list()
        _variables = list()
        ZONE = list()
        DT = list()

        title, _variables, ZONE, DT, lineCount = readDat(dat, title, _variables,
                                                         ZONE, DT)

        self.headerLinesCount = lineCount

        titleString = ''
        for line in title:
            titleString += line

        titleString.replace('\n', '')
        titleString.replace('"', '')
        titleString = re.split('=', titleString)
        self.TECTitle = titleString[1].replace('\n', '').strip()

        variableString = ''
        for line in _variables:
            variableString += line
        variableString.replace('\n', '')
        self.variables = re.findall(r'\S+', variableString)
        self.attributes = re.findall(r'\S+', variableString)
        self.variables.pop(0)
        self.attributes.pop(0)
        self.variables[0] = self.variables[0].replace('=', '')
        self.attributes[0] = self.attributes[0].replace('=', '')
        self.attributeList()

        zoneString = ''
        for line in ZONE:
            zoneString += line
        zoneSplit = re.split(',', zoneString)
        zoneSplit[0] = zoneSplit[0].replace(' ZONE ', '')
        for unit in zoneSplit:
            self.composition.update({unit.split('=')[0]:
                                     unit.split('=')[1].strip()})

        DTstring = ''
        for line in DT:
            DTstring += line
        DTstring = DTstring.replace(' DT=(', '')
        DTstring = DTstring.replace(' \n', '')
        DTstring = DTstring.replace(')\n', '')
        vtype = re.split('\s', DTstring.strip())
        self.variableType = vtype

    def readVariables(self, dat):
        lineCounter = int(ceil(float(self.composition['N'])/5))
        variables = self.variables
        totalVaraibles = len(variables)

        readCounter = 0
        variableCounter = 0
        data = list()
        mesh = list()
        for i in range(self.headerLinesCount, len(dat)):
            row = re.findall(r'\S+', dat[i])
            for number in row:
                data.append(number)
            readCounter += 1

            if ((readCounter == lineCounter) and
                    (variableCounter < totalVaraibles)):
                variables[variableCounter] = {str(variables[variableCounter]):
                                              data}
                variableCounter += 1
                data = list()
                readCounter = 0
            elif variableCounter >= totalVaraibles:
                polygon = list()
                for node in dat[i].split():
                    polygon.append(int(node))
                mesh.append(polygon)
        self.mesh = mesh

    def makeMeshLayer(self):
        mesh = self.mesh
        Xkey = self.variables[0].keys()[0]
        X = self.variables[0][Xkey]
        self.Xmax = max(X)
        self.Xmin = min(X)
        Ykey = self.variables[1].keys()[0]
        Y = self.variables[1][Ykey]
        self.Ymax = max(Y)
        self.Ymin = min(Y)
        c_folder = self.outDir
        crs = self.crs
        path = os.path.join(c_folder, 'mesh.shp')
        self.layerPath = path
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("val", QVariant.Int))

        writer = QgsVectorFileWriter(path, 'utf-8', fields, QGis.WKBPolygon,
                                     crs, "ESRI Shapefile")
        feat_id = 1
        for polygon in mesh:
            feature = QgsFeature()
            geoString = 'POLYGON (('
            if polygon[-1] == polygon[-2]:
                polygon[-1] = polygon[0]
            else:
                polygon.append(polygon[0])
            for node in polygon:
                geoString += (X[node-1] + " " + Y[node-1] + ",")
            geoString = geoString[:-1] + "))"
            feature.setGeometry(QgsGeometry.fromWkt(geoString))
            feature.setAttributes([feat_id, 1])
            writer.addFeature(feature)
            feat_id += 1
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.meshLayer = layer

    def makeSieve(self):
        layer = self.meshLayer
        sievePath = os.path.join(self.outDir, 'sieve.tif')
        xmin = float(self.Xmin)
        xmax = float(self.Xmax)
        ymin = float(self.Ymin)
        ymax = float(self.Ymax)
        processing.runalg('gdalogr:rasterize',
                          {"INPUT": layer,
                           "FIELD": "val",
                           "DIMENSIONS": 1,
                           "WIDTH": float(self.setting['resolution']),
                           "HEIGHT": float(self.setting['resolution']),
                           "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                           "TFW": 1,
                           "RTYPE": 4,
                           "NO_DATA": -1,
                           "COMPRESS": 0,
                           "JPEGCOMPRESSION": 1,
                           "ZLEVEL": 1,
                           "PREDICTOR": 1,
                           "TILED": False,
                           "BIGTIFF": 0,
                           "EXTRA": '',
                           "OUTPUT": sievePath})
        crs = self.crs

        dataset = gdal.Open(sievePath, GA_Update)
        # band = dataset.GetRasterBand(1)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3826)
        dataset.SetProjection(srs.ExportToWkt())
        # dataset = None

        sieveLayer = QgsRasterLayer(sievePath, QFileInfo(sievePath).baseName())
        self.sieveLayer = sieveLayer
        self.sieveLayer.setCrs(crs)

    def genNodeLayer(self):
        crs = self.crs
        baseName = os.path.splitext(self.fileName)[0]
        path = os.path.join(self.outDir, baseName + '.shp')

        fields = QgsFields()
        for i in range(2, len(self.variables)):
            fieldName = self.variables[i].keys()[0]
            if self.variableType[i] == 'DOUBLE':
                fields.append(QgsField(fieldName, QVariant.Double, len=20))
            elif self.variableType[i] == 'INT':
                fields.append(QgsField(fieldName, QVariant.Int, len=20))

        writer = QgsVectorFileWriter(path, 'utf-8', fields, QGis.WKBPoint,
                                     crs, "ESRI Shapefile")

        Xkey = self.variables[0].keys()[0]
        X = self.variables[0][Xkey]
        Ykey = self.variables[1].keys()[0]
        Y = self.variables[1][Ykey]

        for i in range(0, len(X)):
            geoString = 'POINT (' + str(X[i]) + ' ' + str(Y[i]) + ')'
            attr = list()
            #
            for j in range(2, len(self.variables)):
                fieldName = self.variables[j].keys()[0]
                attr.append(self.variables[j][fieldName][i])
            #
            point = QgsFeature()
            point.setGeometry(QgsGeometry.fromWkt(geoString))
            point.setAttributes(attr)
            writer.addFeature(point)

        del writer
        nodeLayer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.nodeLayer = nodeLayer

    def makeContentLayers(self, fieldKey):
        xmin = float(self.Xmin)
        xmax = float(self.Xmax)
        ymin = float(self.Ymin)
        ymax = float(self.Ymax)
        c_folder = self.outDir

        if len(fieldKey) > 10:
            fieldName = fieldKey[0:10]
        else:
            fieldName = fieldKey

        rasterName = fieldName
        self.iface.messageBar().pushMessage('Loading ' + fieldName + ' from ' +
                                            self.nodeLayer.name())
        processing.runalg('grass7:v.surf.rst',
                          {'input': self.nodeLayer,
                           'where': '',
                           'mask': self.sieveLayer,
                           'zcolumn': fieldName,
                           'tension': 40.0,
                           'segmax': 40.0,
                           'npmin': 300.0,
                           'dmin': float(self.setting['min_Dist']),
                           'dmax': 2.50,
                           'zscale': 1.0,
                           'theta': 0.0,
                           'scalex': 0.0,
                           '-t': False,
                           '-d': False,
                           'GRASS_REGION_PARAMETER':
                           "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                           'GRASS_REGION_CELLSIZE_PARAMETER':
                           float(self.setting['resolution']),
                           'GRASS_SNAP_TOLERANCE_PARAMETER': -1.0,
                           'GRASS_MIN_AREA_PARAMETER': 1.0e-4,
                           'elevation': os.path.join(c_folder, rasterName),
                           'slope': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-slope'),
                           'aspect': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-aspect'),
                           'pcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-pcurv'),
                           'tcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-tcurv'),
                           'mcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-mcurv')
                           })


class TEClayerBox:
    def __init__(self, TECfileObj, attr_ramp):
        self.retriveFromTEC(TECfileObj)
        self.arrangeColorRamp(attr_ramp)
        self.renderAttributeLayers()

    def retriveFromTEC(self, TECObject):
        attrs = dict()
        for attrItem in TECObject.contentLayers:
            attrs.update({attrItem[0]: attrItem[1]})
        self.attrs = attrs
        self.fileName = TECObject.text()

    def arrangeColorRamp(self, attr_ramp):
        defaultStyle = QgsStyleV2().defaultStyle()
        ramp = dict()
        for item in attr_ramp:
            if type(item) == str:
                ramp.update({item: defaultStyle.colorRamp('Greys')})
            else:
                ramp.update({item[0]: item[1]})
        self.colorRamp = ramp

    def renderAttributeLayers(self):
        for key in self.attrs.keys():
            layerId = self.attrs[key]
            colorMap = self.colorRamp[key]
            self.changeLayerColorMap(layerId, colorMap)

    def multiply(self, lst, multiplier):
        for i in range(0, len(lst)):
            if type(lst[i]) == list:
                lst[i] = self.multiply(lst[i], multiplier)
            else:
                lst[i] = lst[i]*multiplier
        return lst

    def add(self, lst, obj):
        for i in range(0, len(lst)):
            if type(lst[i]) == list:
                lst[i] = self.add(lst[i], obj)
            else:
                lst[i] = lst[i] + obj
        return lst

    def changeLayerColorMap(self, layerId, colorMap):
        layer = QgsMapLayerRegistry.instance().mapLayer(layerId)

        provider = layer.dataProvider()
        extent = layer.extent()

        rampStops = colorMap.stops()
        valueList = list()
        colorList = list()

        valueList.append(0.0)
        colorList.append(colorMap.color1())
        for item in rampStops:
            valueList.append(item.offset)
            colorList.append(item.color)
        valueList.append(1.0)
        colorList.append(colorMap.color2())

        stats = provider.bandStatistics(1, QgsRasterBandStats.All, extent, 0)

        Max = stats.maximumValue
        Min = stats.minimumValue
        statRange = Max - Min
        valueList = self.add(self.multiply(valueList, statRange), Min)

        ramplst = list()

        rampItemStr = '<= ' + "%.3f" % valueList[0]
        ramplst.append(
            QgsColorRampShader.ColorRampItem(valueList[0], colorList[0],
                                             rampItemStr))
        for i in range(1, len(valueList)):
            rampItemStr = "%.3f" % valueList[i-1] + ' - ' "%.3f" % valueList[i]
            ramplst.append(
                QgsColorRampShader.ColorRampItem(valueList[i], colorList[i],
                                                 rampItemStr))
        myRasterShader = QgsRasterShader()
        myColorRamp = QgsColorRampShader()

        myColorRamp.setColorRampItemList(ramplst)
        if not colorMap.isDiscrete:
            myColorRamp.setColorRampType(QgsColorRampShader.DISCRETE)
        else:
            myColorRamp.setColorRampType(QgsColorRampShader.INTERPOLATED)

        myRasterShader.setRasterShaderFunction(myColorRamp)

        myPseudoRenderer = QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(), layer.type(), myRasterShader)

        layer.setRenderer(myPseudoRenderer)

        layer.triggerRepaint()
