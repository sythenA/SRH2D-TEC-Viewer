
from PyQt4.QtGui import QListWidgetItem
from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerRegistry
from qgis.core import QgsFields, QgsField, QgsProject, QgsRasterLayer, QGis
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsFeature
from qgis.core import QgsGeometry, QgsStyleV2, QgsRasterBandStats
from qgis.core import QgsColorRampShader, QgsSingleBandPseudoColorRenderer
from qgis.core import QgsRasterShader
from osgeo import osr, gdal
from gdalconst import GA_Update
from PyQt4.QtCore import QVariant, QFileInfo, QSettings
from math import ceil, sqrt
from shapely.ops import cascaded_union, polygonize
import numpy as np
from scipy.spatial import Delaunay
from scipy.interpolate import griddata
import re
import subprocess
import os
import processing
import shapely.geometry as geometry


class TECfile(QListWidgetItem):
    def __init__(self, parent, widgetType, filePath, iface):
        super(TECfile, self).__init__(parent, widgetType)
        self.filePath = filePath
        self.fileName = os.path.basename(filePath)
        self.headerLinesCount = 0
        self.iface = iface
        self.TECTile = ''
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')
        self.variables = list()
        self.composition = dict()
        self.variableType = list()
        self.readTEC(filePath)
        self.outDir = ''
        self.xAttr = ''
        self.yAttr = ''
        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        if self.settings.value('crs'):
            self.crs = QgsCoordinateReferenceSystem(self.settings.value('crs'),
                                                    refId)
        else:
            self.crs = QgsCoordinateReferenceSystem(3826, refId)
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

        Xkey = self.variables[0].keys()[0]
        X = self.toFloat(self.variables[0][Xkey])
        self.Xmax = max(X)
        self.Xmin = min(X)
        Ykey = self.variables[1].keys()[0]
        Y = self.toFloat(self.variables[1][Ykey])
        self.Ymax = max(Y)
        self.Ymin = min(Y)

        #  ########  Make Othogonal Grid Points  #########
        points2 = geometry.MultiPoint(list(zip(X, Y)))
        concave_hull2, edge_points2 = self.alpha_shape(points2, alpha=0.01)
        self.hull = concave_hull2
        reso = float(self.settings.value('resolution'))
        self.reso = reso

        X_coordinate = np.arange(self.Xmin, self.Xmax+0.001, reso)
        Y_coordinate = np.arange(self.Ymax, self.Ymin, -reso)
        self.Nx = len(X_coordinate)
        self.Ny = len(Y_coordinate)
        X_ref, Y_ref = np.meshgrid(X_coordinate, Y_coordinate)
        self.X_ref = X_ref
        self.Y_ref = Y_ref

        widx = np.zeros([self.Ny, self.Nx])

        # Identify points inside mesh area
        for i in range(0, len(X_ref)):
            for j in range(0, len(X_ref[0])):
                widx[i, j] = self.within_polygon(
                    geometry.Point(X_ref[i, j], Y_ref[i, j]), concave_hull2, 0)
        self.widx = widx

        # self.makeMeshLayer()
        # self.makeSieve()
        # self.genNodeLayer()

    def alpha_shape(self, points, alpha):
        """
        Compute the alpha shape (concave hull) of a set of points.

        @param points: Iterable container of points.
        @param alpha: alpha value to influence the gooeyness of the border.
                      Smaller numbers don't fall inward as much as larger
                      numbers. Too large, and you lose everything!
        """
        if len(points) < 4:
            # When you have a triangle, there is no sense in computing an alpha
            # shape.
            return geometry.MultiPoint(list(points)).convex_hull

        def add_edge(edges, edge_points, coords, i, j):
            """Add a line between the i-th and j-th points, if not in the list
            already"""
            if (i, j) in edges or (j, i) in edges:
                # already added
                return
            edges.add((i, j))
            edge_points.append(coords[[i, j]])

        coords = np.array([point.coords[0] for point in points])

        tri = Delaunay(coords)
        edges = set()
        edge_points = []
        # loop over triangles:
        # ia, ib, ic = indices of corner points of the triangle
        for ia, ib, ic in tri.vertices:
            pa = coords[ia]
            pb = coords[ib]
            pc = coords[ic]

            # Lengths of sides of triangle
            a = sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
            b = sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
            c = sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)

            # Semiperimeter of triangle
            s = (a + b + c)/2.0

            # Area of triangle by Heron's formula
            area = sqrt(s*(s - a)*(s - b)*(s - c))
            try:
                circum_r = a*b*c/(4.0*area)
            except(ZeroDivisionError):
                circum_r = 0

            # Here's the radius filter.
            # print circum_r
            if circum_r < 1.0/alpha:
                add_edge(edges, edge_points, coords, ia, ib)
                add_edge(edges, edge_points, coords, ib, ic)
                add_edge(edges, edge_points, coords, ic, ia)

        m = geometry.MultiLineString(edge_points)
        triangles = list(polygonize(m))
        return cascaded_union(triangles), edge_points

    def within_polygon(self, grid_point, concave_hull, buffer):
        intw = 0
        if grid_point.within(concave_hull.buffer(buffer)):
            intw = 1
        return intw

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

        attrCounter = 0
        for attr in self.attributes:
            if attr[1] == 1:
                attrCounter += 1
        _attrProgress = int(75/attrCounter/3)

        progress = 75
        self.contentLayers = list()
        for attr in self.attributes:
            idx = self.attributes.index(attr) + 2
            if attr[1] == 1:
                self.makeContentLayers(attr[0], idx)
                progress += _attrProgress
                if len(attr[0]) > 10:
                    rasterName = attr[0][0:10]
                else:
                    rasterName = attr[0]
                rasterPath = os.path.join(self.outDir, rasterName + '.tif')
                baseName = QFileInfo(rasterPath).baseName()
                rasterLayer = QgsRasterLayer(rasterPath, baseName)
                rasMapLayer = QgsMapLayerRegistry.instance().addMapLayer(
                    rasterLayer, False)
                progress += _attrProgress
                self.contentLayers.append([attr[0], rasMapLayer.id()])
                group.addLayer(rasterLayer)
                progress += _attrProgress

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

        title, _variables, ZONE, DT, lineCount = readDat(
            dat, title, _variables, ZONE, DT)

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
        vtype = re.split(r'\s', DTstring.strip())
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

    def toFloat(self, array):
        for i in range(0, len(array)):
            array[i] = float(array[i])

        return array

    def makeMeshLayer(self):
        mesh = self.mesh
        #  ########  Make Polygon Mesh Layer  ##########
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
                geoString += (str(X[node-1]) + " " + str(Y[node-1]) + ",")
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
                           "WIDTH": float(self.settings.value('resolution')),
                           "HEIGHT": float(self.settings.value('resolution')),
                           "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin,
                                                        ymax),
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

    def makeContentLayers(self, fieldKey, idx):
        c_folder = self.outDir

        # original grid data
        Xkey = self.variables[0].keys()[0]
        X = self.toFloat(self.variables[0][Xkey])
        Ykey = self.variables[1].keys()[0]
        Y = self.toFloat(self.variables[1][Ykey])
        ZKey = self.variables[idx].keys()[0]
        Z = self.toFloat(self.variables[idx][ZKey])

        if len(fieldKey) > 10:
            fieldName = fieldKey[0:10]
        else:
            fieldName = fieldKey

        rasterName = fieldName

        X_ref = self.X_ref
        Y_ref = self.Y_ref
        widx = self.widx

        driver = gdal.GetDriverByName('GTiff')
        dst_filename = os.path.join(c_folder, rasterName+'.tif')
        dataset = driver.Create(dst_filename, self.Nx, self.Ny, 1,
                                gdal.GDT_Float32)

        dataset.SetProjection(str(self.crs.toWkt()))
        geotransform = (self.Xmin, self.reso, 0, self.Ymax, 0, -self.reso)
        dataset.SetGeoTransform(geotransform)

        ValueArray = np.zeros([self.Ny, self.Nx])

        # Interpolate on grid data using new orthogonal grids coordinate
        points = list()
        for i in range(0, len(X_ref)):
            points = points + zip(X_ref[i, :], Y_ref[i, :])

        Values = griddata(zip(X, Y), Z, points)

        for i in range(0, len(X_ref)):
            ValueArray[i, :] = Values[i*self.Nx: (i+1)*self.Nx]

        for i in range(0, len(widx)):
            for j in range(0, len(widx[i])):
                if int(widx[i, j]) == 0:
                    ValueArray[i, j] = -9999

        # ######  Create Empty geotiff  ######

        band = dataset.GetRasterBand(1)
        band.SetNoDataValue(-9999)  # Set no data value to -9999 in raster file
        band.WriteArray(ValueArray)
        dataset.FlushCache()


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
